# GraphSight

Self-Verifying Visual Diagram Intelligence

GraphSight converts complex visual diagrams into verified, explainable, and queryable semantic graphs.

Unlike conventional diagram-to-graph pipelines, GraphSight tracks visual evidence for nodes and relationships, detects conflicting interpretations, and can re-analyze uncertain regions before exposing the resulting graph.

```text
Diagram -> Extract -> Verify -> Graph -> Reason
```

This repository is an honest vertical slice. It includes a working FastAPI backend, React workspace UI, GIR schema, upload validation, job records, deterministic graph queries, semantic diff, evidence-backed demo extraction, CLI commands, tests, and Docker wiring. The bundled extractor is a labelled mock/baseline provider for local development; it does not claim model accuracy or benchmark results.

## Demo

```bash
docker compose up --build
```

Open `http://localhost:3000`, upload a diagram image, run analysis, click graph edges, inspect evidence, and ask graph-topology questions such as:

```text
What path connects Router A to Server C?
What is connected to Router A?
What happens if Firewall B is removed?
```

Benchmark results: pending

## Why GraphSight

GraphSight is built around evidence-backed graph reconstruction:

- every node and edge links to evidence;
- confidence is a configurable score, not a claimed calibrated probability;
- verification checks are stored;
- conflicts are first-class records;
- graph questions are answered by deterministic algorithms.

## Architecture

```text
apps/api      FastAPI application
apps/web      React + TypeScript visual workspace
graphsight    Core Python package shared by API and CLI
domain_packs  Extensible class and rule packs
synthetic     Small synthetic sample generator
benchmark     Evaluation entrypoint
tests         Unit and integration tests
```

The current pipeline is:

```text
upload -> validation -> document record -> analysis job -> mock extraction -> GIR -> verification -> query/export
```

Provider boundaries are intentionally simple:

- OCR providers return text regions.
- Object detectors return symbol candidates.
- Connector detectors return pixel connector evidence.
- VLM providers are optional and never required for local demo mode.

## Quick Start

Backend only:

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e ".[dev]"
uvicorn apps.api.graphsight_api.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

CLI:

```bash
graphsight analyze examples/network-demo.gir.json
graphsight verify examples/network-demo.gir.json
graphsight diff examples/network-demo.gir.json examples/network-demo-v2.gir.json
```

## GIR Format

GraphSight Intermediate Representation is versioned as `gir_version: "1.0"` and contains:

- `document`
- `pages`
- `nodes`
- `edges`
- `labels`
- `connectors`
- `evidence`
- `conflicts`
- `uncertainties`
- `metadata`

See [docs/gir.md](docs/gir.md).

## API

- `POST /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `POST /api/v1/documents/{id}/analyze`
- `GET /api/v1/jobs/{id}`
- `GET /api/v1/documents/{id}/graph`
- `GET /api/v1/documents/{id}/evidence`
- `POST /api/v1/graphs/{id}/query`
- `POST /api/v1/graphs/{id}/verify`
- `POST /api/v1/graphs/{id}/diff`
- `GET /api/v1/health`
- `GET /api/v1/ready`

## Evaluation Methodology

Benchmark scripts live under `benchmark/`. They report only measured results from reproducible inputs. No synthetic or mock result is presented as real model performance.

## Roadmap

1. Replace mock OCR/detection with optional PaddleOCR and YOLO/RT-DETR adapters.
2. Add OpenCV preprocessing representations with coordinate transforms.
3. Expand connector topology and junction reasoning.
4. Add review persistence backed by PostgreSQL.
5. Add self-correction crops and revision history.
6. Add multi-document entity matching and visual semantic diff overlays.

## Development

```bash
ruff check .
pytest
cd apps/web && npm run build
```

## License

MIT

