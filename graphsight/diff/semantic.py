from __future__ import annotations

from pydantic import BaseModel, Field

from graphsight.core.gir import GIR


class SemanticDiff(BaseModel):
    added_nodes: list[str] = Field(default_factory=list)
    removed_nodes: list[str] = Field(default_factory=list)
    modified_nodes: list[str] = Field(default_factory=list)
    added_edges: list[str] = Field(default_factory=list)
    removed_edges: list[str] = Field(default_factory=list)
    reversed_edges: list[str] = Field(default_factory=list)


def diff_gir(old: GIR, new: GIR) -> SemanticDiff:
    old_nodes = {node.id: node for node in old.nodes}
    new_nodes = {node.id: node for node in new.nodes}
    old_edges = {edge.id: edge for edge in old.edges}
    new_edges = {edge.id: edge for edge in new.edges}
    old_pairs = {(edge.source, edge.target): edge.id for edge in old.edges}
    new_pairs = {(edge.source, edge.target): edge.id for edge in new.edges}

    return SemanticDiff(
        added_nodes=sorted(set(new_nodes) - set(old_nodes)),
        removed_nodes=sorted(set(old_nodes) - set(new_nodes)),
        modified_nodes=sorted(
            node_id
            for node_id in set(old_nodes) & set(new_nodes)
            if old_nodes[node_id].model_dump(exclude={"confidence"})
            != new_nodes[node_id].model_dump(exclude={"confidence"})
        ),
        added_edges=sorted(set(new_edges) - set(old_edges)),
        removed_edges=sorted(set(old_edges) - set(new_edges)),
        reversed_edges=sorted(
            old_pairs[pair]
            for pair in old_pairs
            if (pair[1], pair[0]) in new_pairs and pair not in new_pairs
        ),
    )

