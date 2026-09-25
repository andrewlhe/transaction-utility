"""Tkinter GUI for the Transaction Utility (CSV/XLSX transaction settlement).

This is the front-end launched by ``main.py``. Other tools live under
``apps/`` as separate programs.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Optional

from . import transaction_calculator


def _append_text(widget: tk.Text, text: str) -> None:
    widget.configure(state="normal")
    widget.insert("end", text)
    widget.see("end")
    widget.configure(state="disabled")


def _set_text(widget: tk.Text, text: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("end", text)
    widget.see("end")
    widget.configure(state="disabled")


class TransactionPanel(ttk.Frame):
    input_file: Optional[str] = None

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(side="top", fill="x")
        ttk.Button(top, text="Open", command=self._on_open).pack(side="left")
        ttk.Button(top, text="Calculate", command=self._on_calculate).pack(side="left")
        ttk.Button(top, text="Save", command=self._on_save).pack(side="left")

        opt = ttk.Frame(self)
        opt.pack(side="bottom", fill="x")
        ttk.Label(opt, text="Filter by Name:").pack(side="left")
        self.filter_var = tk.StringVar(value="")
        ttk.Entry(opt, textvariable=self.filter_var, width=24).pack(side="left")

        self.text = tk.Text(self, wrap="word", font=("Consolas", 11))
        self.text.pack(side="top", fill="both", expand=True)
        _set_text(self.text, "Please choose a transaction file.")

    def _on_open(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose a transaction file",
            filetypes=[("CSV / Excel", "*.csv *.xlsx"), ("All files", "*.*")],
        )
        if not path:
            _set_text(self.text, "Open command cancelled by user.")
            return
        self.input_file = path
        _set_text(self.text, f"File opened: {os.path.basename(path)}.\n")

    def _on_calculate(self) -> None:
        if not self.input_file:
            _set_text(self.text, "Please choose a transaction file.")
            return
        try:
            result = transaction_calculator.calculate(self.input_file, self.filter_var.get())
            _set_text(self.text, transaction_calculator.format_summary(result))
        except PermissionError as e:
            _append_text(
                self.text,
                "Error: cannot read the file (permission denied).\n\n"
                f"{e}\n\n"
                "Possible causes:\n"
                "  1. The file is currently open in Excel or another program -\n"
                "     close it and try again.\n"
                "  2. The file is on OneDrive and only exists in the cloud -\n"
                "     in File Explorer right-click it and choose\n"
                "     'Always keep on this device' to download it, then retry.\n"
                "  3. Try copying the file to a local folder first.",
            )
        except Exception as e:  # noqa: BLE001 - mirror Java's "Error" box
            _append_text(self.text, f"Error\n\n{e}")

    def _on_save(self) -> None:
        path = filedialog.asksaveasfilename(title="Save log", defaultextension=".txt")
        if not path:
            return
        content = self.text.get("1.0", "end")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def main() -> None:
    root = tk.Tk()
    root.title("Transaction Utility")
    root.geometry("900x600")
    TransactionPanel(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
