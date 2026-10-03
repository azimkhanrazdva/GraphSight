from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apps.api.graphsight_api.config import settings
from apps.api.graphsight_api.store import JobRecord, store
from graphsight.diff.semantic import SemanticDiff, diff_gir
from graphsight.pipeline.mock_pipeline import MockDiagramPipeline
from graphsight.query.engine import GraphQueryEngine, QueryResult
from graphsight.security.uploads import UploadRejected
from graphsight.verification.engine import VerificationEngine

app = FastAPI(title="GraphSight API", version="0.1.0")
UPLOAD_FILE = File(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    job_id: str


class QueryRequest(BaseModel):
    question: str


class DiffRequest(BaseModel):
    old_graph_id: str
    new_graph_id: str


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/ready")
def ready() -> dict[str, str]:
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "ready"}


@app.post("/api/v1/documents")
async def upload_document(file: UploadFile = UPLOAD_FILE) -> dict[str, object]:
    try:
        record = await store.save_upload(file)
    except UploadRejected as exc:
        raise HTTPException(status_code=400, detail={"code": "UPLOAD_REJECTED", "message": str(exc)}) from exc
    return {"document": record.info.model_dump(mode="json")}


@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: str) -> dict[str, object]:
    record = store.documents.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document": record.info.model_dump(mode="json")}


@app.post("/api/v1/documents/{document_id}/analyze", response_model=AnalyzeResponse)
def analyze_document(document_id: str, background: BackgroundTasks) -> AnalyzeResponse:
    if document_id not in store.documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    job = store.create_job(document_id)
    background.add_task(_run_analysis, job.id)
    return AnalyzeResponse(job_id=job.id)


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str) -> JobRecord:
    job = store.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/api/v1/documents/{document_id}/graph")
def get_graph(document_id: str) -> dict[str, object]:
    graph = store.graphs.get(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")
    return graph.model_dump(mode="json")


@app.get("/api/v1/documents/{document_id}/evidence")
def get_evidence(document_id: str) -> dict[str, object]:
    graph = store.graphs.get(document_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")
    return {"evidence": [item.model_dump(mode="json") for item in graph.evidence]}


@app.post("/api/v1/graphs/{graph_id}/query", response_model=QueryResult)
def query_graph(graph_id: str, request: QueryRequest) -> QueryResult:
    graph = store.graphs.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")
    return GraphQueryEngine(graph).answer(request.question)


@app.post("/api/v1/graphs/{graph_id}/verify")
def verify_graph(graph_id: str) -> dict[str, object]:
    graph = store.graphs.get(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found.")
    store.graphs[graph_id] = VerificationEngine().verify(graph)
    return store.graphs[graph_id].model_dump(mode="json")


@app.post("/api/v1/graphs/{graph_id}/diff", response_model=SemanticDiff)
def diff_graph(graph_id: str, request: DiffRequest) -> SemanticDiff:
    old = store.graphs.get(request.old_graph_id or graph_id)
    new = store.graphs.get(request.new_graph_id)
    if not old or not new:
        raise HTTPException(status_code=404, detail="Graph not found.")
    return diff_gir(old, new)


def _run_analysis(job_id: str) -> None:
    job = store.jobs[job_id]
    record = store.documents[job.document_id]
    try:
        store.set_job(job_id, "running")
        store.graphs[record.info.id] = MockDiagramPipeline().analyze(record.info, record.path)
        store.set_job(job_id, "completed")
    except RuntimeError as exc:
        store.set_job(job_id, "failed", str(exc))
    except OSError as exc:
        store.set_job(job_id, "failed", str(exc))
