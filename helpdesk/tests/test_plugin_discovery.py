"""Cold-cache concurrent requests share discovery without bypassing verification."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from helpdesk.api import mobile_signing


class TestPluginDiscovery(unittest.TestCase):
    def test_waiter_reads_published_key_without_request_local_cache(self):
        cache = MagicMock()
        public = {"key_id": "expected", "public_key_pem": "verified by publishing fetch"}
        cache.get_value.side_effect = [None, None, public]
        cache.set.return_value = False
        instance = SimpleNamespace(name="instance", base_url="https://example.test")
        with (
            patch.object(mobile_signing.frappe, "cache", return_value=cache),
            patch.object(mobile_signing.time, "sleep") as sleep,
            patch.object(mobile_signing.requests, "get") as get,
        ):
            self.assertEqual(mobile_signing._fetch_public_key(instance, "expected"), public)
        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(cache.get_value.call_args.kwargs, {"use_local_cache": False})
        get.assert_not_called()

    def test_waiter_does_not_accept_a_different_key(self):
        cache = MagicMock()
        cache.get_value.side_effect = [None, {"key_id": "different"}]
        cache.set.return_value = False
        instance = SimpleNamespace(name="instance", base_url="https://example.test")
        with (
            patch.object(mobile_signing.frappe, "cache", return_value=cache),
            patch.object(mobile_signing.time, "sleep"),
            patch.object(mobile_signing, "_deny", side_effect=ValueError("denied")),
            self.assertRaisesRegex(ValueError, "denied"),
        ):
            mobile_signing._fetch_public_key(instance, "expected")
