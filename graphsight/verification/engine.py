from __future__ import annotations

from graphsight.core.gir import GIR, VerificationCheck, VerificationStatus


class VerificationEngine:
    def verify(self, gir: GIR) -> GIR:
        node_ids = {node.id for node in gir.nodes}
        evidence_ids = {ev.id for ev in gir.evidence}
        for edge in gir.edges:
            checks = [
                VerificationCheck(
                    name="valid_source",
                    passed=edge.source in node_ids,
                    confidence=1.0,
                    message="Source node exists.",
                ),
                VerificationCheck(
                    name="valid_target",
                    passed=edge.target in node_ids,
                    confidence=1.0,
                    message="Target node exists.",
                ),
                VerificationCheck(
                    name="visual_evidence",
                    passed=any(ev_id in evidence_ids for ev_id in edge.evidence_ids),
                    confidence=edge.confidence,
                    message="Edge has linked source evidence.",
                ),
            ]
            edge.checks = checks
            if all(check.passed for check in checks) and edge.confidence >= 0.9:
                edge.verification_status = VerificationStatus.VERIFIED
            elif all(check.passed for check in checks) and edge.confidence >= 0.65:
                edge.verification_status = VerificationStatus.PROBABLE
            elif not checks[0].passed or not checks[1].passed:
                edge.verification_status = VerificationStatus.REJECTED
            else:
                edge.verification_status = VerificationStatus.UNCERTAIN
        return gir

