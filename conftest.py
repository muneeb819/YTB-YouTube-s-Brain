import os
import tempfile
import time
from pathlib import Path

# MUST be set before any ytb import (settings is a module-level singleton).
_tmp = tempfile.mkdtemp(prefix="ytb_test_")
os.environ.setdefault("YTB_SECRET_KEY", "test-secret-key")
os.environ.setdefault("YTB_ADMIN_EMAIL", "admin@testdev.ytb")
os.environ.setdefault("YTB_ADMIN_PASSWORD", "test-admin-pass")
os.environ.setdefault("YTB_DATABASE_URL", f"sqlite:///{(Path(_tmp) / 'test.db').as_posix()}")
os.environ.setdefault("YTB_STORAGE_DIR", str(Path(_tmp) / "workspace"))

# Give the background render executor time to settle in tests.
JOB_SETTLE_SECONDS = 1.5

pytest_plugins: list[str] = []