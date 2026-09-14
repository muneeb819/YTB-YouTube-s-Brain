import importlib
import shutil
import sys

required = [
    "fastapi", "uvicorn", "sqlalchemy", "pydantic_settings",
    "email_validator", "jose", "passlib", "bcrypt", "httpx", "multipart",
]

failed = False

for exe in ["ffmpeg", "ffprobe"]:
    found = shutil.which(exe)
    status = "OK" if found else "MISSING (optional, required for media upload/render)"
    print(f"{exe}: {status}")
    if not found and exe in ("ffmpeg", "ffprobe"):
        failed = False  # optional, do not fail on missing binaries

for mod in required:
    try:
        m = importlib.import_module(mod)
        version = getattr(m, "__version__", "")
        print(f"{mod}: OK {version}")
    except Exception as e:
        failed = True
        print(f"{mod}: MISSING ({e})")

try:
    import bcrypt
    major = int(bcrypt.__version__.split(".")[0])
    if major >= 4:
        print("bcrypt: version 4.x+ is incompatible with passlib 1.7.4 (must pin <4.1)")
        failed = True
except Exception as e:
    failed = True
    print(f"bcrypt: MISSING ({e})")

if failed:
    print("\nDependency check FAILED.")
    sys.exit(1)
print("\nDependency check OK.")