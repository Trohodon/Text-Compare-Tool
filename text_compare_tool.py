import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import difflib
from pathlib import Path


class TextCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VBA/Text Compare Tool")
        self.root.geometry("1400x850")

        self.ignore_whitespace = tk.BooleanVar(value=False)
        self.ignore_blank_lines = tk.BooleanVar(value=False)
        self.show_only_differences = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Text Compare Tool", font=("Segoe UI", 16, "bold")).pack(side="left", padx=(0, 20))

        ttk.Button(top, text="Load Left", command=lambda: self.load_file(self.left_text)).pack(side="left", padx=3)
        ttk.Button(top, text="Load Right", command=lambda: self.load_file(self.right_text)).pack(side="left", padx=3)
        ttk.Button(top, text="Compare", command=self.compare).pack(side="left", padx=3)
        ttk.Button(top, text="Clear", command=self.clear_all).pack(side="left", padx=3)
        ttk.Button(top, text="Save Diff", command=self.save_diff).pack(side="left", padx=3)

        ttk.Checkbutton(top, text="Ignore extra whitespace", variable=self.ignore_whitespace).pack(side="left", padx=12)
        ttk.Checkbutton(top, text="Ignore blank lines", variable=self.ignore_blank_lines).pack(side="left", padx=5)
        ttk.Checkbutton(top, text="Only show differences", variable=self.show_only_differences).pack(side="left", padx=5)

        self.status = ttk.Label(top, text="Paste text on both sides, then click Compare.")
        self.status.pack(side="right")

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=4)

        self.left_text = self._make_text_pane(panes, "LEFT: Original / Expected")
        self.right_text = self._make_text_pane(panes, "RIGHT: Your Transcription")

        bottom = ttk.LabelFrame(self.root, text="Difference Report", padding=6)
        bottom.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.diff_text = tk.Text(bottom, wrap="none", height=16, font=("Consolas", 10), undo=True)
        self.diff_text.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(bottom, orient="vertical", command=self.diff_text.yview)
        yscroll.pack(side="right", fill="y")
        self.diff_text.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.diff_text.xview)
        xscroll.pack(fill="x", padx=8)
        self.diff_text.configure(xscrollcommand=xscroll.set)

        self.diff_text.tag_config("same", foreground="black")
        self.diff_text.tag_config("left", foreground="#b00020")
        self.diff_text.tag_config("right", foreground="#007000")
        self.diff_text.tag_config("info", foreground="#003399")
        self.diff_text.tag_config("warn", foreground="#aa6600")

    def _make_text_pane(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=4)
        parent.add(frame, weight=1)

        text = tk.Text(frame, wrap="none", font=("Consolas", 10), undo=True)
        text.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=yscroll.set)

        return text

    def load_file(self, text_widget):
        path = filedialog.askopenfilename(
            title="Open text/code file",
            filetypes=[
                ("Text / Code files", "*.txt *.bas *.vba *.cls *.frm *.py *.csv"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            data = Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            messagebox.showerror("File Error", f"Could not open file:\n{e}")
            return

        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", data)

    def normalize_lines(self, text):
        lines = text.splitlines()

        if self.ignore_blank_lines.get():
            lines = [line for line in lines if line.strip() != ""]

        if self.ignore_whitespace.get():
            # Keeps wording/order, but ignores indentation and repeated spacing.
            lines = [" ".join(line.strip().split()) for line in lines]

        return lines

    def compare(self):
        left_raw = self.left_text.get("1.0", "end-1c")
        right_raw = self.right_text.get("1.0", "end-1c")

        left = self.normalize_lines(left_raw)
        right = self.normalize_lines(right_raw)

        self.diff_text.delete("1.0", tk.END)

        if left == right:
            self.status.config(text="✅ MATCH: no differences found.")
            self.diff_text.insert(tk.END, "No differences found.\n", "info")
            return

        self.status.config(text="❌ Differences found.")

        matcher = difflib.SequenceMatcher(None, left, right)
        diff_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                if not self.show_only_differences.get():
                    for i, line in enumerate(left[i1:i2], start=i1 + 1):
                        self.diff_text.insert(tk.END, f"  L{i:04d} | {line}\n", "same")
                continue

            diff_count += 1
            self.diff_text.insert(tk.END, f"\n--- Difference {diff_count}: {tag.upper()} ---\n", "info")

            if tag in ("replace", "delete"):
                self.diff_text.insert(tk.END, "Left/original:\n", "warn")
                for i, line in enumerate(left[i1:i2], start=i1 + 1):
                    self.diff_text.insert(tk.END, f"- L{i:04d} | {line}\n", "left")

            if tag in ("replace", "insert"):
                self.diff_text.insert(tk.END, "Right/transcription:\n", "warn")
                for j, line in enumerate(right[j1:j2], start=j1 + 1):
                    self.diff_text.insert(tk.END, f"+ R{j:04d} | {line}\n", "right")

            if tag == "replace":
                self._show_character_hint(left[i1:i2], right[j1:j2])

        self.diff_text.insert(tk.END, f"\nDone. Total difference blocks: {diff_count}\n", "info")

    def _show_character_hint(self, left_lines, right_lines):
        max_pairs = min(len(left_lines), len(right_lines), 4)

        for n in range(max_pairs):
            a = left_lines[n]
            b = right_lines[n]

            if a == b:
                continue

            idx = 0
            limit = min(len(a), len(b))
            while idx < limit and a[idx] == b[idx]:
                idx += 1

            self.diff_text.insert(tk.END, f"  First character mismatch near column {idx + 1}\n", "info")
            self.diff_text.insert(tk.END, f"  Left : {a[max(0, idx-30):idx+50]}\n", "left")
            self.diff_text.insert(tk.END, f"  Right: {b[max(0, idx-30):idx+50]}\n", "right")

    def save_diff(self):
        diff = self.diff_text.get("1.0", "end-1c")
        if not diff.strip():
            messagebox.showinfo("Nothing to Save", "Run a comparison first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save diff report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            Path(path).write_text(diff, encoding="utf-8")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{e}")
            return

        messagebox.showinfo("Saved", "Diff report saved.")

    def clear_all(self):
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)
        self.diff_text.delete("1.0", tk.END)
        self.status.config(text="Cleared.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TextCompareApp(root)
    root.mainloop()
