import shutil
for x in ["ffmpeg","ffprobe"]:
    print(x, "OK" if shutil.which(x) else "MISSING")
try:
    import httpx; print("Python dependencies: OK")
except Exception as e: print("Python dependencies: MISSING",e)
