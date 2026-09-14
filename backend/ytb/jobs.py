import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .db import SessionLocal
from .media import render_trim
from .models import Job, MediaAsset

logger = logging.getLogger("ytb.jobs")

executor = ThreadPoolExecutor(max_workers=2)


def submit_render(job_id: int, asset_id: int, start: float, duration: float | None):
    executor.submit(_render, job_id, asset_id, start, duration)


def _render(job_id, asset_id, start, duration):
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            raise RuntimeError(f"Job {job_id} not found")
        asset = db.get(MediaAsset, asset_id)
        if asset is None:
            raise RuntimeError(f"Media asset {asset_id} not found")
        job.state = "RUNNING"
        job.error = ""
        db.commit()

        out = Path(settings.ytb_storage_dir) / "renders" / f"job_{job_id}.mp4"
        out.parent.mkdir(parents=True, exist_ok=True)
        render_trim(asset.path, str(out), start, duration)

        job.state = "COMPLETED"
        job.output_json = json.dumps({"path": str(out)})
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("Render failed for job %s asset %s", job_id, asset_id)
        job = db.get(Job, job_id)
        if job is not None:
            job.state = "FAILED"
            job.error = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Could not persist FAILED state for job %s", job_id)
        else:
            logger.error("Job %s disappeared while rendering", job_id)
    finally:
        db.close()


def recover_interrupted_jobs():
    """Mark jobs that were queued/running when the process last died."""
    db = SessionLocal()
    try:
        interrupted = (
            db.query(Job)
            .filter(Job.state.in_(["QUEUED", "RUNNING"]))
            .all()
        )
        for job in interrupted:
            job.state = "FAILED"
            job.error = "Interrupted: service restarted before the job completed"
        db.commit()
        if interrupted:
            logger.warning("Recovered %d interrupted job(s)", len(interrupted))
    except Exception:
        db.rollback()
        logger.exception("Interrupted-job recovery failed")
    finally:
        db.close()