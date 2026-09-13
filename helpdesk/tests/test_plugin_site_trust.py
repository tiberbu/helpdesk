"""The discovery origin is local configuration, not caller identity."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from helpdesk.api import mobile_signing as signing


class TestSiteTrust(unittest.TestCase):
    def test_configured_origin_overrides_legacy_record_url(self):
        record = SimpleNamespace(name="legacy-scope", enabled=1, users=[], base_url="https://ignored.example.test")
        with patch.object(signing.frappe, "conf", {"careverse_url": "https://cv.example.test", "careverse_trust_record": "legacy-scope"}), patch.object(signing.frappe, "get_doc", return_value=record) as get_doc:
            result = signing.configured_instance()
        self.assertEqual(result.base_url, "https://cv.example.test")
        self.assertEqual(result.name, "legacy-scope")
        get_doc.assert_called_once_with("HD CareVerse Instance", "legacy-scope")

    def test_hostname_selects_existing_mapping_without_extra_configuration(self):
        record = SimpleNamespace(name="cv.example.test", enabled=1, users=[])
        with patch.object(signing.frappe, "conf", {"careverse_url": "https://cv.example.test"}), patch.object(signing.frappe, "get_doc", return_value=record) as get_doc:
            signing.configured_instance()
        get_doc.assert_called_once_with("HD CareVerse Instance", "cv.example.test")

    def test_missing_or_unsafe_origin_fails_closed(self):
        for origin in ("", "http://cv.example.test", "https://user:password@cv.example.test", "https://cv.example.test/path", "https://cv.example.test?key=x"):
            with self.subTest(origin=origin), patch.object(signing.frappe, "conf", {"careverse_url": origin}), patch.object(signing, "_deny", side_effect=frappe.AuthenticationError), self.assertRaises(frappe.AuthenticationError):
                signing.configured_instance()

    def test_signed_arguments_require_no_instance(self):
        request = Request(EnvironBuilder(method="GET", query_string={"user_id": "reporter@example.test", "request_id": "a" * 32}).get_environ())
        self.assertEqual(set(signing.signed_arguments(request)), {"user_id", "request_id"})

    def test_caller_cannot_supply_instance_or_discovery_origin(self):
        for field in ("instance_id", "origin", "careverse_url"):
            request = Request(EnvironBuilder(method="GET", query_string={"user_id": "reporter@example.test", "request_id": "a" * 32, field: "untrusted"}).get_environ())
            with self.subTest(field=field), patch.object(signing, "_deny", side_effect=frappe.AuthenticationError), self.assertRaises(frappe.AuthenticationError):
                signing.signed_arguments(request)
