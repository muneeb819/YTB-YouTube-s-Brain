import shutil
import subprocess

import pytest

from ytb.config import settings
from ytb.media import _has_video, render_trim

pytestmark = pytest.mark.skipif(
    shutil.which(settings.ffmpeg_bin) is None or shutil.which(settings.ffprobe_bin) is None,
    reason="ffmpeg/ffprobe not available",
)


@pytest.fixture(scope="module")
def source_video(tmp_path_factory):
    out = tmp_path_factory.mktemp("media") / "src.mp4"
    r = subprocess.run(
        [
            settings.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=duration=3:size=160x120:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(out),
        ],
        capture_output=True,
    )
    if r.returncode != 0:
        pytest.skip(f"cannot create sample video: {r.stderr[-200:]}")
    return out


def test_render_trim_preserves_video(source_video, tmp_path):
    # Regression: a mid-stream trim must keep the video track. An output-side
    # `-ss` + `-c copy` used to produce an audio-only "render" while exiting 0.
    dst = tmp_path / "trim.mp4"
    render_trim(str(source_video), str(dst), start=0.5, duration=1.0)
    assert dst.is_file() and dst.stat().st_size > 0
    assert _has_video(str(dst))


def test_render_trim_full_clip(source_video, tmp_path):
    dst = tmp_path / "full.mp4"
    render_trim(str(source_video), str(dst))
    assert dst.is_file() and dst.stat().st_size > 0
    assert _has_video(str(dst))