"""Standalone CLI to run the contract analysis pipeline without DB or worker."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from config import validate_openai_config
from pipeline.contract_analysis import run_contract_analysis
from pipeline.errors import PipelineError

logger = logging.getLogger(__name__)

_CLI_FAILURE_MESSAGE = "Pipeline CLI failed. Check logs for details."
_WORKER_AI_ROOT = Path(__file__).resolve().parents[2]


def _default_output_path(analysis_job_id: str) -> Path:
    return _WORKER_AI_ROOT / "outputs" / f"{analysis_job_id}.result.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run LegalMove contract analysis pipeline on local image files. "
            "Does not use PostgreSQL or the worker. Requires OPENAI_API_KEY in .env."
        ),
    )
    parser.add_argument(
        "--analysis-job-id",
        default="local-test-001",
        help="Analysis job ID for Langfuse grouping and default output filename.",
    )
    parser.add_argument(
        "--original-file-path",
        required=True,
        help="Path to the original contract image.",
    )
    parser.add_argument(
        "--amendment-file-path",
        required=True,
        help="Path to the amendment image.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save result JSON to ./outputs/{analysis_job_id}.result.json",
    )
    parser.add_argument(
        "--output",
        help="Explicit output file path (implies save). Overrides the default outputs/ path.",
    )
    return parser


def _resolve_output_path(args: argparse.Namespace) -> Path | None:
    if args.output:
        return Path(args.output)
    if args.save:
        return _default_output_path(args.analysis_job_id)
    return None


def _write_report(output_path: Path, report: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    output_path.write_text(payload + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    args = _build_parser().parse_args(argv)
    output_path = _resolve_output_path(args)

    try:
        validate_openai_config()
        report = run_contract_analysis(
            analysis_job_id=args.analysis_job_id,
            original_file_path=args.original_file_path,
            amendment_file_path=args.amendment_file_path,
        )
    except PipelineError as exc:
        logger.exception("Pipeline failed for job %s", args.analysis_job_id)
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        logger.exception("Unexpected CLI failure for job %s", args.analysis_job_id)
        print(_CLI_FAILURE_MESSAGE, file=sys.stderr)
        return 1

    payload = json.dumps(report, indent=2, ensure_ascii=False)
    print(payload)

    if output_path is not None:
        try:
            _write_report(output_path, report)
            logger.info("Saved pipeline result to %s", output_path)
        except OSError:
            logger.exception("Failed to write output file %s", output_path)
            print(_CLI_FAILURE_MESSAGE, file=sys.stderr)
            return 1

    return 0
