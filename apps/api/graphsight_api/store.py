from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from apps.api.graphsight_api.config import settings
from graphsight.core.gir import GIR, DocumentInfo
from graphsight.security.uploads import sha256_file, validate_image_upload


@dataclass
class DocumentRecord:
    info: DocumentInfo
    path: Path


@dataclass
class JobRecord:
    id: str
    document_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    error: str | None = None


class MemoryStore:
    def __init__(self) -> None:
        self.documents: dict[str, DocumentRecord] = {}
        self.jobs: dict[str, JobRecord] = {}
        self.graphs: dict[str, GIR] = {}

    async def save_upload(self, upload: UploadFile) -> DocumentRecord:
        settings.storage_dir.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(delete=False) as tmp:
            shutil.copyfileobj(upload.file, tmp)
            tmp_path = Path(tmp.name)
        try:
            internal_name, mime = validate_image_upload(
                tmp_path,
                upload.filename or "upload",
                settings.max_upload_mb,
                settings.max_image_pixels,
            )
            target = settings.storage_dir / internal_name
            tmp_path.replace(target)
            doc_id = internal_name.rsplit(".", 1)[0]
            info = DocumentInfo(
                id=doc_id,
                filename=Path(upload.filename or "upload").name,
                mime_type=mime,
                sha256=sha256_file(target),
            )
            record = DocumentRecord(info=info, path=target)
            self.documents[doc_id] = record
            return record
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def create_job(self, document_id: str) -> JobRecord:
        job_id = f"job_{document_id}"
        now = datetime.now(UTC)
        job = JobRecord(id=job_id, document_id=document_id, status="queued", created_at=now, updated_at=now)
        self.jobs[job_id] = job
        return job

    def set_job(self, job_id: str, status: str, error: str | None = None) -> None:
        job = self.jobs[job_id]
        job.status = status
        job.error = error
        job.updated_at = datetime.now(UTC)


store = MemoryStore()

