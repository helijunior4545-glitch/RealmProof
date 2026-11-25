"""Explicit local-only settings; never select this module in production."""
import os
import secrets
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_key = _root / ".realmproof-local-key"
try:
    fd = os.open(_key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    pass
else:
    with os.fdopen(fd, "w") as stream:
        stream.write(secrets.token_urlsafe(64))
_secret = _key.read_text().strip()
if len(_secret) < 50:
    raise RuntimeError("Invalid local key; remove .realmproof-local-key and retry.")
os.environ["DJANGO_SECRET_KEY"] = _secret
os.environ["DJANGO_DEBUG"] = "1"
os.environ["DATABASE_URL"] = ""
os.environ["DJANGO_ALLOWED_HOSTS"] = "localhost,127.0.0.1,[::1]"
os.environ["DJANGO_STATIC_ROOT"] = str(_root / "staticfiles")
from .settings import *  # noqa: F403,E402
