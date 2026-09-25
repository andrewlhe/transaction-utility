"""Settle pairwise balances from a transaction CSV or XLSX.

Mirrors TransactionUtility.java. Input is a UTF-8 CSV (or an .xlsx file with
the same column layout) with a header row. Columns used (0-indexed):
    0  date
    1  seller
    2  item           ("PAYMENT" flips payer/payee)
    6  currencyLocal
    7  currencySettlement
    9  totalLocal     (e.g. "$123.45" or a plain number)
    10 totalSettlement
    11 payer
    12 payee

Payer/payee are truncated to 3 characters; "XDD" is normalised to "XHY".
Self-payments are dropped. The result is a netting: for every A<->B pair,
only the one who still owes a positive amount is reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .common import load_table

IDENTIFIER_LENGTH = 3
_SELF_REPLACEMENT = "XDD"
_SELF_REPLACEMENT_TO = "XHY"


def _norm_party(name: str) -> str:
    # Java: (payer + "   ").substring(0, 3) == left-justify to 3 chars.
    p = (name + "   ")[:3]
    if p == _SELF_REPLACEMENT:
        p = _SELF_REPLACEMENT_TO
    return p


def _parse_money(token: str) -> float:
    # Java: Double.parseDouble(tokens[9].trim().substring(1)) -> strip leading "$".
    # Excel cells may be plain numbers (no $), so tolerate both.
    s = token.strip()
    if s.startswith("$"):
        s = s[1:]
    return float(s)


@dataclass
class TxEntry:
    line_no: int
    date: str
    seller: str
    item: str
    currency_local: str
    currency_settlement: str
    total_local: float
    total_settlement: float
    payer: str
    payee: str


@dataclass
class SettleResult:
    details: List[str] = field(default_factory=list)
    net: Dict[Tuple[str, str], float] = field(default_factory=dict)  # ((pair, currency)) -> amount owed
    elapsed_ms: int = 0
    sheet_name: Optional[str] = None


def calculate(path: str, filter_text: str = "") -> SettleResult:
    result = SettleResult()
    filter_names: Set[str] = set()
    if "," in filter_text:
        filter_names = {t.strip() for t in filter_text.split(",") if t.strip()}
    elif filter_text:
        filter_names.add(filter_text.strip())

    rows, sheet_name = load_table(path, want_sheet=True)  # type: ignore[misc]
    result.sheet_name = sheet_name

    # Skip header.
    if not rows:
        return result
    rows = rows[1:]

    # first[(pair, currency)] accumulates per settling currency, so different
    # currencies are never added together.
    first: Dict[Tuple[str, str], float] = {}
    line_count = 0
    import time
    start = time.perf_counter()

    for tokens in rows:
        line_count += 1
        if len(tokens) < 13:
            continue
        date = tokens[0].strip()
        seller = tokens[1].strip()
        item = tokens[2].strip()
        currency_local = tokens[6].strip()
        currency_settlement = tokens[7].strip()
        total_local = _parse_money(tokens[9])
        total_settlement = _parse_money(tokens[10])
        payer = _norm_party(tokens[11])
        payee = _norm_party(tokens[12])

        if payer == payee:
            result.details.append(f"{line_count:5d}: Skipped ({payee:>3s} paid for {payer:>3s})")
            continue
        if item == "PAYMENT":
            payer, payee = payee, payer

        key = payer + payee
        first[(key, currency_settlement)] = (
            first.get((key, currency_settlement), 0.0) + total_settlement
        )

        if filter_names and payer not in filter_names and payee not in filter_names:
            continue
        if item == "PAYMENT":
            result.details.append(
                f"{line_count:5d}: {payee:>3s} paid {total_settlement:.2f} {currency_settlement} "
                f"({total_local:.2f} {currency_local}) to {payer:>3s} at {date} via {seller}"
            )
        else:
            result.details.append(
                f"{line_count:5d}: {payee:>3s} paid {total_settlement:.2f} {currency_settlement} "
                f"({total_local:.2f} {currency_local}) for {payer:>3s} at {date} at {seller}"
            )

    # Netting pass: within each currency (TreeMap iteration == sorted keys).
    # Group first by currency so EUR never nets against USD.
    by_currency: Dict[str, Dict[str, float]] = {}
    for (key, cur), amount in first.items():
        by_currency.setdefault(cur, {})[key] = amount

    third: Dict[Tuple[str, str], float] = {}
    for cur in sorted(by_currency):
        first_cur = by_currency[cur]
        second: Dict[str, float] = {}
        for key in sorted(first_cur):
            reversed_key = key[3:6] + key[0:3]
            if reversed_key in second:
                second[reversed_key] -= first_cur[key]
            elif key in second:
                # The Java original read second.get(reversedKey) here (a latent bug that
                # is unreachable given sorted iteration); we reproduce the intended
                # behaviour of adding to the existing key.
                second[key] += first_cur[key]
            else:
                second[key] = first_cur[key]

        for key in sorted(second):
            amount = second[key]
            if amount < 0.0:
                third[(key[3:6] + key[0:3], cur)] = -amount
            else:
                third[(key, cur)] = amount

    result.elapsed_ms = int((time.perf_counter() - start) * 1000)
    for (key, cur) in sorted(third):
        party1, party2 = key[0:3], key[3:6]
        amount = third[(key, cur)]
        if filter_names and party1 not in filter_names and party2 not in filter_names:
            continue
        # Only show meaningful balances (>= 1 in the settling currency) in the
        # final report; the calculation above keeps all values so nothing is lost.
        if amount < 1.0:
            continue
        result.net[(key, cur)] = amount
    return result


def format_summary(result: SettleResult) -> str:
    lines: List[str] = list(result.details)
    lines.append("")
    if result.sheet_name:
        lines.append(f"Sheet: {result.sheet_name}")
    lines.append(f"Calculation finished in {result.elapsed_ms / 1000.0:.6f} ms")
    lines.append("")
    for (key, cur) in sorted(result.net, key=lambda k: (k[1], k[0])):
        party1, party2 = key[0:3], key[3:6]
        lines.append(
            f"{party1} needs to pay {party2} {result.net[(key, cur)]:.2f} {cur}"
        )
    return "\n".join(lines)
