"""CLI for the Transaction Utility (transaction settlement only).

Other tools live under ``apps/`` as standalone programs.

Usage:
    python -m transaction_utility tx-calc --input transactions.csv [--filter "ABC,DEF"] [--save out.txt]
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import transaction_calculator


def _cmd_tx_calc(args: argparse.Namespace) -> int:
    result = transaction_calculator.calculate(args.input, args.filter or "")
    print(transaction_calculator.format_summary(result))
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(transaction_calculator.format_summary(result))
        print(f"Saved log to {args.save}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="transaction_utility",
        description="Transaction Utility - transaction settlement (other tools live under apps/)",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("tx-calc", help="Settle pairwise balances from a transaction CSV/XLSX")
    sp.add_argument("--input", required=True)
    sp.add_argument("--filter", default="")
    sp.add_argument("--save", default=None)
    sp.set_defaults(func=_cmd_tx_calc)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
