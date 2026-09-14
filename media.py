import json, subprocess
from pathlib import Path
from .config import settings

def probe(path: str) -> dict:
    cmd=[settings.ffprobe_bin,"-v","error","-show_format","-show_streams","-of","json",path]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True)
    return json.loads(p.stdout)

def render_trim(src: str, dst: str, start: float=0.0, duration: float|None=None):
    cmd=[settings.ffmpeg_bin,"-y","-i",src,"-ss",str(max(0,start))]
    if duration is not None:
        cmd += ["-t",str(max(0.1,duration))]
    cmd += ["-map","0","-c","copy",dst]
    p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode != 0:
        # Re-encode fallback for containers/codecs that cannot stream-copy.
        cmd=[settings.ffmpeg_bin,"-y","-ss",str(max(0,start)),"-i",src]
        if duration is not None: cmd += ["-t",str(max(0.1,duration))]
        cmd += ["-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-movflags","+faststart",dst]
        p=subprocess.run(cmd,capture_output=True,text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-4000:])
    return dst
