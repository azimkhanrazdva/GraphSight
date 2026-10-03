import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, ArrowRight, Boxes, CheckCircle2, FileUp, Network, Search, ShieldCheck } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

type BBox = { x: number; y: number; width: number; height: number };
type NodeItem = { id: string; type: string; label: string; bbox: BBox; confidence: number; evidence_ids: string[] };
type EdgeItem = { id: string; source: string; target: string; confidence: number; evidence_ids: string[]; verification_status: string };
type EvidenceItem = { id: string; type: string; source: string; confidence: number; bbox?: BBox; geometry?: { points?: { x: number; y: number }[] } };
type GIR = {
  document: { id: string; filename: string };
  pages: { width: number; height: number }[];
  nodes: NodeItem[];
  edges: EdgeItem[];
  evidence: EvidenceItem[];
  conflicts: unknown[];
  metadata: Record<string, string>;
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [imageUrl, setImageUrl] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [graph, setGraph] = useState<GIR | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<string[]>([]);
  const [question, setQuestion] = useState("What path connects Router A to Server C?");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const evidenceById = useMemo(() => new Map(graph?.evidence.map((item) => [item.id, item])), [graph]);

  async function uploadAndAnalyze() {
    if (!file) return;
    setBusy(true);
    setAnswer("");
    const body = new FormData();
    body.append("file", file);
    const uploaded = await fetch(`${API_BASE}/api/v1/documents`, { method: "POST", body }).then((res) => res.json());
    const id = uploaded.document.id;
    setDocumentId(id);
    const job = await fetch(`${API_BASE}/api/v1/documents/${id}/analyze`, { method: "POST" }).then((res) => res.json());
    await fetch(`${API_BASE}/api/v1/jobs/${job.job_id}`).then((res) => res.json());
    const gir = await fetch(`${API_BASE}/api/v1/documents/${id}/graph`).then((res) => res.json());
    setGraph(gir);
    setBusy(false);
  }

  async function ask() {
    if (!documentId) return;
    const result = await fetch(`${API_BASE}/api/v1/graphs/${documentId}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then((res) => res.json());
    setAnswer(result.answer);
    const edgeEvidence = graph?.edges.filter((edge) => result.edge_ids?.includes(edge.id)).flatMap((edge) => edge.evidence_ids) ?? [];
    setSelectedEvidence(edgeEvidence);
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <div className="brand"><Network size={20} /> GraphSight</div>
          <p>From pixels to verifiable structure.</p>
        </div>
        <div className="run-state"><ShieldCheck size={16} /> Evidence-backed demo mode</div>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <label className="dropzone">
            <FileUp size={22} />
            <span>{file ? file.name : "Upload PNG, JPG, or WebP"}</span>
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => {
                const next = event.target.files?.[0] ?? null;
                setFile(next);
                setImageUrl(next ? URL.createObjectURL(next) : "");
              }}
            />
          </label>
          <button className="primary" disabled={!file || busy} onClick={uploadAndAnalyze}>
            <ArrowRight size={16} /> {busy ? "Analyzing..." : "Analyze"}
          </button>
          <Metric label="Verified" value={graph?.edges.filter((edge) => edge.verification_status === "verified").length ?? 0} />
          <Metric label="Uncertain" value={graph?.edges.filter((edge) => edge.verification_status === "uncertain").length ?? 0} />
          <Metric label="Conflicts" value={graph?.conflicts.length ?? 0} />
        </aside>

        <section className="panes">
          <Panel title="Original Diagram" icon={<Boxes size={16} />}>
            <DiagramView graph={graph} imageUrl={imageUrl} selectedEvidence={selectedEvidence} evidenceById={evidenceById} />
          </Panel>
          <Panel title="Semantic Graph" icon={<Network size={16} />}>
            <GraphView graph={graph} onSelect={(ids) => setSelectedEvidence(ids)} />
          </Panel>
        </section>

        <section className="bottom">
          <div className="query">
            <label>Graph query</label>
            <div className="query-row">
              <input value={question} onChange={(event) => setQuestion(event.target.value)} />
              <button onClick={ask} disabled={!graph}><Search size={16} /></button>
            </div>
            <output>{answer || "Deterministic graph answers appear here."}</output>
          </div>
          <EvidenceList graph={graph} selectedEvidence={selectedEvidence} />
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return <section className="panel"><h2>{icon}{title}</h2>{children}</section>;
}

function DiagramView({ graph, imageUrl, selectedEvidence, evidenceById }: { graph: GIR | null; imageUrl: string; selectedEvidence: string[]; evidenceById: Map<string, EvidenceItem> }) {
  if (!imageUrl) return <div className="empty">Upload a diagram to inspect source evidence.</div>;
  const page = graph?.pages[0];
  const viewBox = page ? `0 0 ${page.width} ${page.height}` : "0 0 900 420";
  return (
    <div className="diagram">
      <img src={imageUrl} alt="Uploaded diagram" />
      {graph && <svg viewBox={viewBox} aria-label="Evidence overlay">
        {graph.nodes.map((node) => <rect key={node.id} className="node-box" x={node.bbox.x} y={node.bbox.y} width={node.bbox.width} height={node.bbox.height} />)}
        {selectedEvidence.map((id) => {
          const ev = evidenceById.get(id);
          const points = ev?.geometry?.points;
          return points && points.length > 1 ? <line key={id} className="evidence-line" x1={points[0].x} y1={points[0].y} x2={points[1].x} y2={points[1].y} /> : null;
        })}
      </svg>}
    </div>
  );
}

function GraphView({ graph, onSelect }: { graph: GIR | null; onSelect: (ids: string[]) => void }) {
  if (!graph) return <div className="empty">Run analysis to see reconstructed topology.</div>;
  return (
    <div className="graph-list">
      {graph.edges.map((edge) => {
        const source = graph.nodes.find((node) => node.id === edge.source);
        const target = graph.nodes.find((node) => node.id === edge.target);
        return (
          <button key={edge.id} className="edge-row" onClick={() => onSelect(edge.evidence_ids)}>
            <span>{source?.label}</span>
            <ArrowRight size={18} />
            <span>{target?.label}</span>
            <Confidence value={edge.confidence} />
            {edge.verification_status === "verified" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          </button>
        );
      })}
    </div>
  );
}

function Confidence({ value }: { value: number }) {
  return <span className="confidence">{Math.round(value * 100)}%</span>;
}

function EvidenceList({ graph, selectedEvidence }: { graph: GIR | null; selectedEvidence: string[] }) {
  const evidence = graph?.evidence.filter((item) => selectedEvidence.length === 0 || selectedEvidence.includes(item.id)) ?? [];
  return (
    <div className="evidence">
      <h2>Evidence</h2>
      {evidence.length === 0 ? <p>Select an edge to inspect supporting pixels.</p> : evidence.map((item) => (
        <div key={item.id} className="evidence-row">
          <span>{item.type}</span>
          <code>{item.source}</code>
          <Confidence value={item.confidence} />
        </div>
      ))}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

