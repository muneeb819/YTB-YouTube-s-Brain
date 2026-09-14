import json
import subprocess

from .config import settings


def run(cmd: list[str], timeout: int | None = 120):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe(path: str) -> dict:
    cmd = [settings.ffprobe_bin, "-v", "error", "-show_format", "-show_streams", "-of", "json", path]
    p = run(cmd)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-4000:] or f"ffprobe failed with code {p.returncode}")
    return json.loads(p.stdout)


def render_trim(src: str, dst: str, start: float = 0.0, duration: float | None = None):
    cmd = [settings.ffmpeg_bin, "-y", "-i", src, "-ss", str(max(0, start))]
    if duration is not None:
        cmd += ["-t", str(max(0.1, duration))]
    cmd += ["-map", "0", "-c", "copy", dst]
    p = run(cmd, timeout=3600)
    if p.returncode != 0:
        cmd = [settings.ffmpeg_bin, "-y", "-ss", str(max(0, start)), "-i", src]
        if duration is not None:
            cmd += ["-t", str(max(0.1, duration))]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart", dst]
        p = run(cmd, timeout=3600)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-4000:])
    return dst