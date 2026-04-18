from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "src" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.case_sanitizer import sanitize_cases  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Saneia casos legados persistidos no banco.")
    parser.add_argument("--case-id", default=None, help="Executa o saneamento apenas para um caso.")
    parser.add_argument("--use-llm", action="store_true", help="Permite uso de LLM durante a reanálise.")
    parser.add_argument("--dry-run", action="store_true", help="Calcula mudanças sem persistir no banco.")
    args = parser.parse_args()

    payload = sanitize_cases(
        case_id=args.case_id,
        allow_llm=args.use_llm,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
