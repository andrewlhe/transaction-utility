# Transaction Utility (Python rewrite)

Python port of the transaction settlement part of the original
`Transaction Utility.jar`. Opens a CSV or XLSX file and produces a netting
report: who owes whom and how much.

## Quick start

```bash
# GUI
python main.py

# CLI
python -m transaction_utility tx-calc --input transactions.csv --filter "ABC,DEF"
```

## Input format

CSV or XLSX with a header row. Columns used (0-indexed):

| Index | Column            | Example          |
|-------|-------------------|------------------|
| 0     | date              | `2024-01-01`     |
| 1     | seller            | `Amazon`         |
| 2     | item              | `ITEM` / `PAYMENT` |
| 6     | currencyLocal     | `USD`            |
| 7     | currencySettlement| `USD`            |
| 9     | totalLocal        | `$100.00` or `100.0` |
| 10    | totalSettlement   | `$100.00` or `100.0` |
| 11    | payer             | `Alice`          |
| 12    | payee             | `Bob`            |

## Output

For each pair, the final report shows only balances **>= 1 USD**. Small
amounts are excluded to reduce noise (the full calculation is still performed).

## Structure

```
Transaction-Utility/
  main.py                    # Launch GUI
  transaction_utility/
    gui.py                   # Tkinter GUI
    transaction_calculator.py # Settlement logic
    common.py                # Shared helpers (CSV/XLSX reader)
```

Other utilities from the original JAR (duplicate finder, file manager,
camera-sequence tools, photo tools, GPX, vocabulary) live in
`C:\Users\helew\Documents\utilities`.
