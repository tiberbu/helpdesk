"""Media validation and bounded private reads."""

import base64
import io
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from PIL import Image

from helpdesk.api import plugin_media


class TestPluginMedia(unittest.TestCase):
    def test_all_supported_image_formats(self):
        for fmt, name, mime in [
            ("PNG", "screen.png", "image/png"),
            ("JPEG", "photo.jpg", "image/jpeg"),
            ("WEBP", "photo.webp", "image/webp"),
        ]:
            with self.subTest(fmt=fmt):
                stream = io.BytesIO()
                Image.new("RGB", (2, 2), "white").save(stream, format=fmt)
                files = plugin_media.validate(
                    [
                        {
                            "file_name": name,
                            "content_type": mime,
                            "content_base64": base64.b64encode(
                                stream.getvalue()
                            ).decode(),
                        }
                    ]
                )
                self.assertEqual(files[0]["content"], stream.getvalue())

    def test_native_video_with_image_extension_is_not_listed(self):
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(b"\x00\x00\x00\x18ftypmp42video")
            stream.flush()
            file = SimpleNamespace(
                name="file",
                attached_to_doctype="HD Ticket Comment",
                attached_to_name="comment",
                is_private=1,
                is_remote_file=False,
                is_folder=False,
                file_name="video.png",
                file_size=20,
                check_permission=lambda *_: None,
                get_full_path=lambda: stream.name,
            )
            with patch.object(plugin_media.frappe, "get_doc", return_value=file):
                self.assertEqual(
                    plugin_media._files(["file"], "HD Ticket Comment", "comment"), []
                )

    def test_actual_read_limit_ignores_stale_size_metadata(self):
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(b"x" * (plugin_media.MAX_FILE_BYTES + 1))
            stream.flush()
            file = SimpleNamespace(file_size=1, get_full_path=lambda: stream.name)
            with (
                patch.object(
                    plugin_media.frappe, "throw", side_effect=frappe.ValidationError
                ),
                self.assertRaises(frappe.ValidationError),
            ):
                plugin_media._read(file)
