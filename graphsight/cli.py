from __future__ import annotations

import argparse
import json
from pathlib import Path

from graphsight.core.gir import GIR
from graphsight.diff.semantic import diff_gir
from graphsight.query.engine import GraphQueryEngine
from graphsight.verification.engine import VerificationEngine


def verify(path: Path) -> None:
    gir = VerificationEngine().verify(GIR.model_validate_json(path.read_text()))
    print(gir.model_dump_json(indent=2))


def query(path: Path, question: str) -> None:
    gir = GIR.model_validate_json(path.read_text())
    print(GraphQueryEngine(gir).answer(question).model_dump_json(indent=2))


def diff(old: Path, new: Path) -> None:
    result = diff_gir(GIR.model_validate_json(old.read_text()), GIR.model_validate_json(new.read_text()))
    print(result.model_dump_json(indent=2))


def analyze(path: Path) -> None:
    print(
        json.dumps(
            {
                "message": "Image analysis is exposed through the API in this vertical slice.",
                "input": str(path),
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="graphsight")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("path", type=Path)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("path", type=Path)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("path", type=Path)
    query_parser.add_argument("question")

    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("old", type=Path)
    diff_parser.add_argument("new", type=Path)

    args = parser.parse_args()
    if args.command == "analyze":
        analyze(args.path)
    elif args.command == "verify":
        verify(args.path)
    elif args.command == "query":
        query(args.path, args.question)
    elif args.command == "diff":
        diff(args.old, args.new)
