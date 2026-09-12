"""Development-only signed RPC checks; database fixtures are rolled back."""
import base64
import hashlib
import json
import uuid
import io
from PIL import Image
from pypdf import PdfWriter
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import frappe
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from unittest.mock import MagicMock, patch
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from helpdesk.api import plugin as mobile
from helpdesk.api.mobile_signing import verify_request

frappe.init(site='hd-dev.tiberbu.app', sites_path='/home/ubuntu/frappe-bench/sites')
frappe.connect()
frappe.set_user('Administrator')
frappe.flags.mute_emails = True
key = Ed25519PrivateKey.generate()
pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
user = 'signed-rpc-' + uuid.uuid4().hex[:8] + '@example.test'
key_id = hashlib.sha256(pem.encode()).hexdigest()[:16]
instance_id = 'validation-' + uuid.uuid4().hex
trust = {key_id: {'public_key_pem': pem, 'allowed_users': [user]}}

def request(endpoint, method='GET', values=None, age=0):
    values = {**(values or {}), 'user_id': user, 'instance_id': instance_id, 'request_id': uuid.uuid4().hex}
    path = '/api/method/helpdesk.api.plugin.' + endpoint
    query = urlencode(values) if method == 'GET' else ''
    body = b'' if method == 'GET' else json.dumps(values, separators=(',', ':')).encode()
    stamp = (datetime.now(timezone.utc) - timedelta(seconds=age)).strftime('%Y-%m-%dT%H:%M:%SZ')
    target = path + ('?' + query if query else '')
    canonical = '\n'.join([method, target, stamp, hashlib.sha256(body).hexdigest()])
    headers = {'X-AC-Key-Id':key_id,'X-AC-Timestamp':stamp,'X-AC-Signature':base64.b64encode(key.sign(canonical.encode())).decode()}
    return Request(EnvironBuilder(path=path,query_string=query,method=method,data=body,content_type='application/json',headers=headers).get_environ())

def call(fn, method='GET', **values):
    frappe.local.request = request(fn.__name__, method, values)
    return fn(**values)

try:
    frappe.get_doc({'doctype':'User','email':user,'first_name':'Signed RPC Validation','send_welcome_email':0,'user_type':'Website User','roles':[{'role':'Helpdesk Customer'}]}).insert()
    frappe.get_doc({'doctype':'HD CareVerse Instance','instance_id':instance_id,'enabled':1,'base_url':'https://careverse.example.test','users':[{'careverse_user':user,'helpdesk_user':user,'enabled':1}]}).insert()
    agents=[]
    for index in range(2):
        agent=f"plugin-agent-{index}-{uuid.uuid4().hex[:8]}@example.test"
        frappe.get_doc({'doctype':'User','email':agent,'first_name':'Plugin Support Validation','send_welcome_email':0,'roles':[{'role':'Agent'}]}).insert()
        frappe.get_doc({'doctype':'HD Agent','user':agent,'agent_name':'Plugin Validation Agent'}).insert()
        agents.append(agent)
    frappe.get_doc({'doctype':'Assignment Rule','name':'plugin-validation-'+uuid.uuid4().hex,
                    'document_type':'HD Ticket','priority':10000,'rule':'Round Robin',
                    'assign_condition':f"plugin_instance in {repr([instance_id, 'second-'+instance_id])}",
                    'assignment_days':[{'day':day} for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']], 'users':[{'user':agent} for agent in agents]}).insert()
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = 200
    response.iter_content.return_value = [json.dumps({'message':{'status':'success','data':{'key_id':key_id,'public_key_pem':pem}}}).encode()]
    fetch = patch('helpdesk.api.mobile_signing.requests.get', return_value=response)
    mocked_fetch = fetch.start()
    frappe.set_user('Guest')
    call(mobile.get_bootstrap); print('PASS signed guest bootstrap as allowed customer')
    assert frappe.session.user == 'Guest'
    call(mobile.get_counties);call(mobile.get_subcounties,county='Mombasa');call(mobile.get_facilities)
    payload=dict(source='HMIS',external_reference_id=uuid.uuid4().hex,reporter={'name':'Jane Doe','email':user,'facility':'Facility Name'},description='Plain <script> text',priority='Medium',category='System Error')
    image_bytes=io.BytesIO()
    Image.new('RGB',(2,2),(12,24,uuid.uuid4().int % 255)).save(image_bytes,format='PNG')
    pdf_bytes=io.BytesIO()
    writer=PdfWriter();writer.add_blank_page(width=100,height=100);writer.write(pdf_bytes)
    uploads=[{'file_name':'registration.png','content_type':'image/png','content_base64':base64.b64encode(image_bytes.getvalue()).decode()},
             {'file_name':'issue.pdf','content_type':'application/pdf','content_base64':base64.b64encode(pdf_bytes.getvalue()).decode()}]
    payload['attachments']=uploads
    created=call(mobile.create_ticket,'POST',**payload)['data']
    tid=created['ticket_id']
    assert created['reused'] is False and isinstance(created['assigned_to'],list)
    repeated=call(mobile.create_ticket,'POST',**{**payload,'description':'Retry changed text'})['data']
    assert repeated['ticket_id']==tid and repeated['reused'] is True
    assert created['assigned_to']==[agents[0]] and repeated['assigned_to']==[agents[0]]
    doc=call(mobile.get_ticket,ticket_id=tid)['data']
    assert 'Plain &lt;script&gt;' in doc['description_html']
    assert doc['reporter']==payload['reporter'] and doc['source']=='HMIS'
    assert doc['external_reference_id']==payload['external_reference_id']
    assert len(call(mobile.list_tickets,email=user)['data']['items'])==1
    assert len(created['attachments'])==2 and repeated['attachments']==created['attachments']
    initial=call(mobile.list_attachments,ticket_id=tid)['data']['items']
    assert len(initial)==2 and all(item['is_private'] and item['event_id'] is None for item in initial)
    for item,expected in zip(initial,[image_bytes.getvalue(),pdf_bytes.getvalue()]):
        fetched=call(mobile.download_attachment,ticket_id=tid,attachment_id=item['attachment_id'])['data']
        decoded=base64.b64decode(fetched['content_base64'])
        assert decoded==expected and fetched['sha256']==hashlib.sha256(expected).hexdigest()
    assert len(call(mobile.get_thread,ticket_id=tid)['data']['initial_attachments'])==2
    try:call(mobile.create_ticket,'POST',**{**payload,'attachments':[]});raise AssertionError('Changed retry files')
    except frappe.ValidationError:pass
    attached_message=call(mobile.send_message,'POST',ticket_id=tid,attachments=[uploads[0]])['data']
    event=next(e for e in call(mobile.get_thread,ticket_id=tid)['data']['items'] if e['id']==attached_message['message_id'])
    assert len(event['attachments'])==1 and event['attachments']==attached_message['attachments']
    print('PASS atomic create files, retry metadata, private download and attachment-only message')
    for bad in [dict(uploads[0],file_name='clip.mp4',content_type='video/mp4'),
                dict(uploads[0],file_name='../image.png'),dict(uploads[0],content_base64='!invalid'),
                dict(uploads[0],content_base64=base64.b64encode(b'not an image').decode()),
                dict(uploads[0],content_base64='A'*2796208)]:
        try:call(mobile.create_ticket,'POST',**{**payload,'external_reference_id':uuid.uuid4().hex,'attachments':[bad]});raise AssertionError('Invalid attachment accepted')
        except frappe.ValidationError:pass
    assert len(call(mobile.list_tickets)['data']['items'])==1
    print('PASS video, traversal, invalid Base64, spoofed MIME and size rejection before creation')
    print('PASS contract payload, stable retry, reporter metadata and assignment shape')
    for fn,values in [(mobile.list_tickets,{'email':'another@example.test'}),(mobile.create_ticket,{**payload,'reporter':{**payload['reporter'],'email':'another@example.test'}})]:
        try:call(fn,'POST' if fn==mobile.create_ticket else 'GET',**values);raise AssertionError('Reporter spoofing')
        except frappe.PermissionError:pass
    print('PASS reporter spoofing denied on create and list')
    assert doc['raised_by']==user
    tid=doc['name'];call(mobile.send_message,'POST',ticket_id=tid,content='Test <script> message')
    assert any(x['kind']=='message' and '&lt;script&gt;' in x['content_html'] for x in call(mobile.get_thread,ticket_id=tid)['data']['items'])
    assert any(x['name']==tid for x in call(mobile.list_tickets)['data']['items'])
    print('PASS signed create/list/public thread')
    try:call(mobile.get_ticket,ticket_id='TKT-26-09-10-00002');raise AssertionError('Cross-user read')
    except frappe.PermissionError:print('PASS cross-user denied')
    frappe.set_user('Administrator');frappe.get_doc('HD Ticket',tid).new_internal_note('INTERNAL SIGNING CHECK');frappe.set_user('Guest')
    assert 'INTERNAL SIGNING CHECK' not in str(call(mobile.get_thread,ticket_id=tid))
    print('PASS internal note hidden')
    from helpdesk.api import plugin_media
    frappe.set_user('Administrator')
    internal=frappe.get_list('HD Ticket Comment',filters={'reference_ticket':tid,'is_internal':1},pluck='name')[0]
    hidden_file=plugin_media.save(plugin_media.validate([uploads[0]]),'HD Ticket Comment',internal)[0]['attachment_id']
    public=frappe.get_doc('HD Ticket',tid).new_comment('Agent public attachment')
    public_file=plugin_media.save(plugin_media.validate([uploads[1]]),'HD Ticket Comment',public)[0]['attachment_id']
    frappe.set_user('Guest')
    visible_ids={item['attachment_id'] for item in call(mobile.list_attachments,ticket_id=tid)['data']['items']}
    assert public_file in visible_ids and hidden_file not in visible_ids
    call(mobile.download_attachment,ticket_id=tid,attachment_id=public_file)
    try:call(mobile.download_attachment,ticket_id=tid,attachment_id=hidden_file);raise AssertionError('Internal file download')
    except frappe.PermissionError:pass
    print('PASS native agent public file accessible; internal-note file hidden and denied')

    frappe.set_user('Administrator')
    from helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity import log_ticket_activity
    log_ticket_activity(tid, 'set status to Open')
    frappe.set_user('Guest')
    assert any(e['kind']=='activity' for e in call(mobile.get_thread,ticket_id=tid)['data']['items'])
    print('PASS customer ticket activity visible')
    frappe.set_user(user)
    assert not frappe.get_list('HD Ticket Activity', filters={'ticket':'TKT-26-09-10-00002'}, fields=['name'])
    frappe.set_user('Guest')
    print('PASS other-ticket activity filtered')
    for label,req,keys in [
        ('expired',request('get_bootstrap',age=60),trust),
        ('future',request('get_bootstrap',age=-60),trust),
        ('unknown key',request('get_bootstrap'),{}),
        ('unmapped identity',request('get_bootstrap'),{key_id:{'public_key_pem':pem,'allowed_users':[]}}),
    ]:
        try:verify_request(req,keys,'get_bootstrap','helpdesk.api.plugin');raise AssertionError(label)
        except frappe.AuthenticationError:print('PASS rejected '+label)
    req=request('send_message','POST',{'ticket_id':tid,'content':'original'})
    req._cached_data=req.get_data().replace(b'original',b'tampered')
    try:verify_request(req,trust,'send_message','helpdesk.api.plugin');raise AssertionError('Tampered body')
    except frappe.AuthenticationError:print('PASS tampered body rejected')
    req=request('get_bootstrap');frappe.local.request=req;mobile.get_bootstrap()
    try:mobile.get_bootstrap();raise AssertionError('Replay')
    except frappe.AuthenticationError:print('PASS replay rejected')
    assert mocked_fetch.call_count == 1
    assert mocked_fetch.call_args.args[0] == 'https://careverse.example.test/api/method/careverse_hq.api.hmis_signing.get_public_key'
    print('PASS configured public-key discovery and caching')
    frappe.set_user('Administrator')
    second_id='second-'+instance_id
    frappe.get_doc({'doctype':'HD CareVerse Instance','instance_id':second_id,'enabled':1,'base_url':'https://careverse.example.test','users':[{'careverse_user':user,'helpdesk_user':user,'enabled':1}]}).insert()
    original_instance=instance_id
    instance_id=second_id
    frappe.set_user('Guest')
    assert call(mobile.list_tickets)['data']['items']==[]
    try:call(mobile.get_ticket,ticket_id=tid);raise AssertionError('Cross-instance read')
    except frappe.PermissionError:pass
    try:call(mobile.download_attachment,ticket_id=tid,attachment_id=initial[0]['attachment_id']);raise AssertionError('Cross-instance download')
    except frappe.PermissionError:pass
    other=call(mobile.create_ticket,'POST',**payload)['data']
    assert other['ticket_id']!=tid and other['reused'] is False
    try:call(mobile.download_attachment,ticket_id=other['ticket_id'],attachment_id=initial[0]['attachment_id']);raise AssertionError('Cross-ticket file ID')
    except frappe.PermissionError:pass
    print('PASS cross-instance and cross-ticket attachment denial')
    assert other['assigned_to']==[agents[1]], other
    instance_id=original_instance
    other_source=call(mobile.create_ticket,'POST',**{**payload,'source':'Mobile'})['data']
    assert other_source['ticket_id']!=tid
    assert other_source['assigned_to']==[agents[0]], other_source
    print('PASS native round robin rotates and retry does not reassign')
    print('PASS instance isolation and source-scoped reference IDs')
    first_page=call(mobile.list_tickets,user=user,facility=payload['reporter']['facility'],limit=1)['data']
    assert first_page['items'][0]['ticket_id']==other_source['ticket_id'] and first_page['has_more']
    second_page=call(mobile.list_tickets,user=user,offset=first_page['next_offset'],limit=1)['data']
    assert second_page['items'][0]['ticket_id']==tid and not second_page['has_more']
    assert call(mobile.list_tickets,facility='No matching facility')['data']['items']==[]
    try:call(mobile.list_tickets,user='another@example.test');raise AssertionError('Other user filter')
    except frappe.PermissionError:pass
    print('PASS facility/user filters preserve scope and latest-first pagination')

    from helpdesk.api import plugin_media
    from pathlib import Path
    import os
    unique_image=io.BytesIO()
    Image.frombytes('RGB',(8,8),os.urandom(8*8*3)).save(unique_image,format='PNG')
    failing_upload=[dict(uploads[0],content_base64=base64.b64encode(unique_image.getvalue()).decode())]
    failed_reference=uuid.uuid4().hex
    written=[]
    save_files=plugin_media.save
    def fail_after_file_save(files,doctype,name):
        saved=save_files(files,doctype,name)
        written.extend(frappe.get_doc('File',row['attachment_id']).get_full_path() for row in saved)
        raise OSError('Simulated storage failure after file creation')
    with patch.object(plugin_media,'save',side_effect=fail_after_file_save):
        try:call(mobile.create_ticket,'POST',**{**payload,'external_reference_id':failed_reference,'attachments':failing_upload});raise AssertionError('Expected storage failure')
        except OSError:pass
    assert written and all(Path(path).exists() for path in written)
    frappe.db.rollback()  # Same full rollback performed by the HTTP framework on an exception.
    frappe.set_user('Administrator')
    assert not frappe.get_list('HD Ticket',filters={'external_reference_id':failed_reference},pluck='name')
    assert not any(Path(path).exists() for path in written)
    print('PASS storage failure rolls back ticket, File records and new private blob')

finally:
    if 'fetch' in globals(): fetch.stop()
    frappe.db.rollback()
    frappe.destroy()
