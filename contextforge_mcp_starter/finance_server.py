"""Run the isolated Yahoo Finance MCP server on this Mac's loopback port 8003."""

import argparse
import os
from pathlib import Path
import stat

import uvicorn

from finance import FinanceTools
from server import create_app


def read_private_token(path: Path) -> str:
    """Read only a regular, owner-only token file; never print its contents."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "r") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise RuntimeError("MCP token file must be a regular file owned by the current user.")
        if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_size > 4096:
            raise RuntimeError("MCP token file must have mode 600 and contain a bounded secret.")
        try:
            token = stream.read().strip()
        except UnicodeDecodeError:
            raise RuntimeError("Finance MCP token must be a single printable ASCII token.") from None
    if len(token) < 32:
        raise RuntimeError("Finance MCP token must contain at least 32 characters.")
    if not token.isascii() or not token.isprintable() or any(character.isspace() for character in token):
        raise RuntimeError("Finance MCP token must be a single printable ASCII token without whitespace.")
    return token


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, help="Private mode-600 token file; otherwise use MCP_TOKEN")
    args = parser.parse_args()
    try:
        if args.token_file:
            os.environ["MCP_TOKEN"] = read_private_token(args.token_file)
        app = create_app(finance=FinanceTools(), port=8003,
                         server_name="Yahoo Finance Mac", enable_workflow=False)
    except (RuntimeError, OSError) as error:
        raise SystemExit(str(error)) from None
    uvicorn.run(app, host="127.0.0.1", port=8003, access_log=False, log_level="info")


if __name__ == "__main__":
    main()
