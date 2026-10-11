"""Token-file security tests; credentials here are invented fixtures."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from finance_server import read_private_token
import mac_host


class PrivateTokenTests(unittest.TestCase):
    def test_owner_only_token_can_be_read_without_exposing_it(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("fixture-" + "x" * 32 + "\n")
            os.chmod(path, 0o600)
            self.assertEqual(read_private_token(path), "fixture-" + "x" * 32)

    def test_group_readable_token_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("fixture-" + "x" * 32)
            os.chmod(path, 0o640)
            with self.assertRaisesRegex(RuntimeError, "mode 600"):
                read_private_token(path)

    def test_symbolic_link_to_token_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("fixture-" + "x" * 32)
            os.chmod(path, 0o600)
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(OSError):
                read_private_token(link)

    def test_short_token_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            path.write_text("short-fixture")
            os.chmod(path, 0o600)
            with self.assertRaisesRegex(RuntimeError, "at least 32"):
                read_private_token(path)

    def test_token_file_rejects_internal_spaces_newlines_and_non_ascii(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "token"
            for value in ["Bearer " + "x" * 32, "x" * 32 + "\n" + "y" * 32, "é" * 40]:
                path.write_text(value)
                path.chmod(0o600)
                with self.subTest(kind="invalid-token-format"), self.assertRaisesRegex(RuntimeError, "ASCII"):
                    read_private_token(path)


class TunnelStatusTests(unittest.TestCase):
    def test_expired_quick_tunnel_is_not_reported_as_a_current_public_endpoint(self):
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "tunnel.log").write_text(
                "https://old-fixture.trycloudflare.com\nRegistered tunnel connection\nUnauthorized: Tunnel not found\n")
            with patch.object(mac_host, "RUNTIME", runtime), patch.object(mac_host, "service_state", return_value={"running": True}):
                status = mac_host.host_status()
            self.assertEqual(status["tunnel_status"], "expired")
            self.assertIsNone(status["public_endpoint"])

    def test_new_registered_tunnel_supersedes_earlier_expiration(self):
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "tunnel.log").write_text(
                "https://old-fixture.trycloudflare.com\nUnauthorized: Tunnel not found\n"
                "https://new-fixture.trycloudflare.com\nRegistered tunnel connection\n")
            with patch.object(mac_host, "RUNTIME", runtime), patch.object(mac_host, "service_state", return_value={"running": True}):
                status = mac_host.host_status()
            self.assertEqual(status["tunnel_status"], "connected")
            self.assertEqual(status["public_endpoint"], "https://new-fixture.trycloudflare.com/mcp")


if __name__ == "__main__":
    unittest.main()
