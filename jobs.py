import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from .models import Job, MediaAsset
from .db import SessionLocal
from .media import render_trim
from .config import settings

executor=ThreadPoolExecutor(max_workers=2)

def submit_render(job_id:int, asset_id:int, start:float, duration:float|None):
    executor.submit(_render,job_id,asset_id,start,duration)

def _render(job_id,asset_id,start,duration):
    db=SessionLocal()
    try:
        job=db.get(Job,job_id); asset=db.get(MediaAsset,asset_id)
        job.state="RUNNING"; db.commit()
        out=Path(settings.ytb_storage_dir)/"renders"/f"job_{job_id}.mp4"
        out.parent.mkdir(parents=True,exist_ok=True)
        render_trim(asset.path,str(out),start,duration)
        job.state="COMPLETED"; job.output_json=json.dumps({"path":str(out)})
        db.commit()
    except Exception as e:
        job=db.get(Job,job_id); job.state="FAILED"; job.error=str(e); db.commit()
    finally: db.close()
