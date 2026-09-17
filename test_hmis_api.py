#!/usr/bin/env python3
"""
Test script for HMIS → Helpdesk API Integration
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
HELPDESK_URL = "https://support.tiberbu.app"
API_KEY = "DZaLRbVp2rXkgTtYBcePQd84xltDsjoT"
API_SECRET = "dRwAbpmgch7ucEex#8I@P.,6;]iOU*i?;dH93LJV8&HLq:}k"


def test_create_ticket():
    """Test creating a ticket"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Create Ticket from HMIS")
    print("="*60)

    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.create_ticket_from_hmis"

    payload = {
        "subject": f"Test Ticket - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "This is a test ticket created via HMIS API integration.\n\n**Test Details:**\n- Module: Patient Management\n- Issue: Cannot save patient record\n- Error: Timeout after 30 seconds",
        "raised_by_email": "test@facility.com",
        "raised_by_name": "Test Implementor",
        "priority": "High",
        # ticket_type and category removed - not configured in this helpdesk
        "external_reference_id": f"HMIS-TEST-{int(datetime.now().timestamp())}",
        "hmis_module": "Patient Management",
        "hmis_url": "https://hmis.example.com/issues/12345",
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }

    print(f"\n📤 Sending request to: {endpoint}")
    print(f"   Subject: {payload['subject']}")
    print(f"   Priority: {payload['priority']}")
    print(f"   HMIS Reference: {payload['external_reference_id']}")

    try:
        response = requests.post(endpoint, json=payload, timeout=30)

        print(f"\n📥 Response: HTTP {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Frappe wraps response in "message" key
            if "message" in result:
                result = result["message"]

            if result.get("success"):
                print(f"\n✅ SUCCESS!")
                print(f"   Ticket ID: {result['ticket_id']}")
                print(f"   Ticket URL: {result['ticket_url']}")
                print(f"   Status: {result['ticket_status']}")
                print(f"   Priority: {result['ticket_priority']}")
                print(f"   Created: {result['created_on']}")
                return result['ticket_id']
            else:
                print(f"\n❌ FAILED!")
                print(f"   Error: {result.get('exception')}")
                print(f"   Type: {result.get('exc_type')}")
                return None
        else:
            print(f"\n❌ HTTP ERROR!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None

    except requests.exceptions.Timeout:
        print(f"\n❌ REQUEST TIMEOUT!")
        print(f"   The helpdesk server did not respond within 30 seconds")
        return None

    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR!")
        print(f"   Cannot connect to {HELPDESK_URL}")
        print(f"   Check your internet connection and firewall")
        return None

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR!")
        print(f"   {type(e).__name__}: {str(e)}")
        return None


def test_get_status(ticket_id):
    """Test getting ticket status"""
    print("\n" + "="*60)
    print(f"🧪 TEST 2: Get Ticket Status - {ticket_id}")
    print("="*60)

    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.get_ticket_status"

    payload = {
        "ticket_id": str(ticket_id),  # Convert to string
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }

    print(f"\n📤 Sending request to: {endpoint}")

    try:
        response = requests.post(endpoint, json=payload, timeout=30)

        print(f"\n📥 Response: HTTP {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Frappe wraps response in "message" key
            if "message" in result:
                result = result["message"]

            if result.get("success"):
                print(f"\n✅ SUCCESS!")
                print(f"   Ticket ID: {result['ticket_id']}")
                print(f"   Subject: {result['subject']}")
                print(f"   Status: {result['status']}")
                print(f"   Priority: {result['priority']}")
                print(f"   Raised By: {result['raised_by']}")
                print(f"   Agent Group: {result.get('agent_group', 'Not assigned')}")
                print(f"   Created: {result['created_on']}")
                print(f"   Modified: {result['modified_on']}")
                return True
            else:
                print(f"\n❌ FAILED!")
                print(f"   Error: {result.get('exception')}")
                return False
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_update_ticket(ticket_id):
    """Test updating a ticket"""
    print("\n" + "="*60)
    print(f"🧪 TEST 3: Update Ticket - {ticket_id}")
    print("="*60)

    endpoint = f"{HELPDESK_URL}/api/method/helpdesk.api.external_integration.update_ticket_from_hmis"

    payload = {
        "ticket_id": str(ticket_id),  # Convert to string
        "comment": f"Test comment added via API at {datetime.now().strftime('%H:%M:%S')}",
        "priority": "Medium",
        "api_key": API_KEY,
        "api_secret": API_SECRET
    }

    print(f"\n📤 Sending request to: {endpoint}")
    print(f"   Adding comment: {payload['comment']}")
    print(f"   Changing priority to: {payload['priority']}")

    try:
        response = requests.post(endpoint, json=payload, timeout=30)

        print(f"\n📥 Response: HTTP {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Frappe wraps response in "message" key
            if "message" in result:
                result = result["message"]

            if result.get("success"):
                print(f"\n✅ SUCCESS!")
                print(f"   Ticket updated: {result['ticket_id']}")
                print(f"   New Status: {result['ticket_status']}")
                print(f"   New Priority: {result['ticket_priority']}")
                return True
            else:
                print(f"\n❌ FAILED!")
                print(f"   Error: {result.get('exception')}")
                return False
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 HMIS → Helpdesk API Integration Test Suite")
    print("="*60)
    print(f"   Helpdesk URL: {HELPDESK_URL}")
    print(f"   API Key: {API_KEY[:20]}..." if len(API_KEY) > 20 else f"   API Key: {API_KEY}")
    print("="*60)

    # Check if credentials are set
    if API_KEY == "REPLACE_WITH_YOUR_API_KEY" or API_SECRET == "REPLACE_WITH_YOUR_API_SECRET":
        print("\n❌ ERROR: API credentials not configured!")
        print("\nPlease edit this script and set:")
        print("  1. API_KEY = 'your-api-key-from-hd-settings'")
        print("  2. API_SECRET = 'your-api-secret-from-hd-settings'")
        print("\nTo get credentials:")
        print("  1. Log in to Helpdesk as Administrator")
        print("  2. Go to: Settings → HD Settings")
        print("  3. Enable 'External API Integration'")
        print("  4. Set API Key and API Secret")
        print("  5. Save")
        sys.exit(1)

    # Test 1: Create ticket
    ticket_id = test_create_ticket()

    if not ticket_id:
        print("\n" + "="*60)
        print("❌ TEST SUITE FAILED - Could not create ticket")
        print("="*60)
        sys.exit(1)

    # Test 2: Get ticket status
    test_get_status(ticket_id)

    # Test 3: Update ticket
    test_update_ticket(ticket_id)

    # Summary
    print("\n" + "="*60)
    print("✅ TEST SUITE COMPLETED!")
    print("="*60)
    print(f"\nCreated test ticket: {ticket_id}")
    print(f"View in helpdesk: {HELPDESK_URL}/helpdesk/tickets/{ticket_id}")
    print("\n💡 Next steps:")
    print("  1. Check the ticket in the helpdesk UI")
    print("  2. Verify HMIS reference fields are populated")
    print("  3. Integrate this code into your HMIS system")
    print("\n📚 Full documentation: /home/ubuntu/frappe-bench/apps/helpdesk/HMIS_API_INTEGRATION.md")
    print("="*60)


if __name__ == "__main__":
    main()
