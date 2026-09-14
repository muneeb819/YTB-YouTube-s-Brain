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


def _has_video(path: str) -> bool:
    try:
        info = probe(path)
    except Exception:
        return False
    return any(s.get("codec_type") == "video" for s in info.get("streams", []))


def render_trim(src: str, dst: str, start: float = 0.0, duration: float | None = None):
    safe_start = max(0.0, start)
    safe_duration = max(0.1, duration) if duration is not None else None

    # Fast path: stream-copy with INPUT-side seeking. Seeking on the input starts
    # at the nearest keyframe, which keeps the video track intact. Output-side
    # seeking + `-c copy` can silently produce a file with zero video frames
    # (ffmpeg exits 0), so we verify the result has a video stream before
    # accepting it.
    cmd = [settings.ffmpeg_bin, "-y", "-ss", str(safe_start), "-i", src]
    if safe_duration is not None:
        cmd += ["-t", str(safe_duration)]
    cmd += ["-map", "0", "-c", "copy", dst]
    p = run(cmd, timeout=3600)
    if p.returncode == 0 and _has_video(dst):
        return dst

    # Fallback: decode + re-encode for containers/codecs that cannot stream-copy,
    # and for copy attempts that produced no usable video track.
    cmd = [settings.ffmpeg_bin, "-y", "-ss", str(safe_start), "-i", src]
    if safe_duration is not None:
        cmd += ["-t", str(safe_duration)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart", dst]
    p = run(cmd, timeout=3600)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-4000:])
    if not _has_video(dst):
        raise RuntimeError("Render produced no video stream")
    return dst