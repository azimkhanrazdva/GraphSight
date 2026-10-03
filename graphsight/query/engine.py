from __future__ import annotations

import re

import networkx as nx
from pydantic import BaseModel

from graphsight.core.gir import GIR


class QueryResult(BaseModel):
    intent: str
    answer: str
    node_ids: list[str] = []
    edge_ids: list[str] = []


class GraphQueryEngine:
    def __init__(self, gir: GIR) -> None:
        self.gir = gir
        self.graph = nx.DiGraph()
        for node in gir.nodes:
            self.graph.add_node(node.id, label=node.label)
        for edge in gir.edges:
            self.graph.add_edge(edge.source, edge.target, edge_id=edge.id)

    def answer(self, question: str) -> QueryResult:
        normalized = question.lower()
        labels = {node.label.lower(): node.id for node in self.gir.nodes}
        mentioned = [node_id for label, node_id in labels.items() if label in normalized]

        path_match = re.search(r"path connects? (.+?) to (.+?)[?.]?$", normalized)
        if path_match:
            source = self._find_node(path_match.group(1), labels)
            target = self._find_node(path_match.group(2), labels)
            if source and target:
                return self._shortest_path(source, target)

        if "connected to" in normalized and mentioned:
            return self._neighbors(mentioned[0])

        if "removed" in normalized and mentioned:
            return self._remove_impact(mentioned[0])

        return QueryResult(
            intent="unknown",
            answer="I could not map that question to a deterministic graph query yet.",
        )

    def _find_node(self, text: str, labels: dict[str, str]) -> str | None:
        text = text.strip().lower()
        if text in labels:
            return labels[text]
        for label, node_id in labels.items():
            if text in label or label in text:
                return node_id
        return None

    def _shortest_path(self, source: str, target: str) -> QueryResult:
        try:
            path = nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return QueryResult(intent="path", answer="No directed path exists.", node_ids=[source, target])
        edge_ids = [
            self.graph.edges[path[index], path[index + 1]]["edge_id"]
            for index in range(len(path) - 1)
        ]
        labels = [self.graph.nodes[node]["label"] for node in path]
        return QueryResult(intent="path", answer=" -> ".join(labels), node_ids=path, edge_ids=edge_ids)

    def _neighbors(self, source: str) -> QueryResult:
        neighbors = sorted(self.graph.successors(source))
        labels = [self.graph.nodes[node]["label"] for node in neighbors]
        return QueryResult(
            intent="neighbors",
            answer=", ".join(labels) if labels else "No outgoing connections.",
            node_ids=[source, *neighbors],
        )

    def _remove_impact(self, source: str) -> QueryResult:
        impacted = sorted(nx.descendants(self.graph, source))
        labels = [self.graph.nodes[node]["label"] for node in impacted]
        return QueryResult(
            intent="what_if_remove",
            answer=(
                "Graph-topological downstream impact: " + ", ".join(labels)
                if labels
                else "No downstream nodes are reachable from this node."
            ),
            node_ids=[source, *impacted],
        )

