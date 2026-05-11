import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import difflib
from pathlib import Path


class TextCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VBA/Text Compare Tool")
        self.root.geometry("1400x850")

        self.ignore_whitespace_only_blank_lines = tk.BooleanVar(value=True)
        self.strip_trailing_spaces = tk.BooleanVar(value=True)
        self.ignore_all_blank_lines = tk.BooleanVar(value=False)
        self.ignore_extra_whitespace = tk.BooleanVar(value=False)
        self.show_only_differences = tk.BooleanVar(value=True)

        self.status_text = tk.StringVar(value="Paste text on both sides, then click Compare.")
        self.jump_var = tk.StringVar(value="No differences")

        self.diff_blocks = []
        self.current_diff_index = -1

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="VBA/Text Compare Tool", font=("Segoe UI", 16, "bold")).pack(side="left", padx=(0, 20))

        ttk.Button(top, text="Load Left", command=lambda: self.load_file(self.left_text)).pack(side="left", padx=3)
        ttk.Button(top, text="Load Right", command=lambda: self.load_file(self.right_text)).pack(side="left", padx=3)
        ttk.Button(top, text="Compare", command=self.compare).pack(side="left", padx=3)
        ttk.Button(top, text="Previous Problem", command=self.prev_difference).pack(side="left", padx=(14, 3))
        ttk.Button(top, text="Next Problem", command=self.next_difference).pack(side="left", padx=3)
        ttk.Button(top, text="Clear", command=self.clear_all).pack(side="left", padx=(14, 3))
        ttk.Button(top, text="Save Diff", command=self.save_diff).pack(side="left", padx=3)

        self.jump_combo = ttk.Combobox(top, textvariable=self.jump_var, state="readonly", width=34)
        self.jump_combo.pack(side="right", padx=(10, 0))
        self.jump_combo.bind("<<ComboboxSelected>>", self._on_jump_selected)
        ttk.Label(top, text="Jump to:").pack(side="right")

        opts = ttk.Frame(self.root, padding=(8, 0, 8, 4))
        opts.pack(fill="x")

        ttk.Checkbutton(
            opts,
            text="Treat blank lines with spaces as blank",
            variable=self.ignore_whitespace_only_blank_lines,
        ).pack(side="left", padx=6)

        ttk.Checkbutton(
            opts,
            text="Ignore trailing spaces",
            variable=self.strip_trailing_spaces,
        ).pack(side="left", padx=6)

        ttk.Checkbutton(
            opts,
            text="Ignore all blank lines",
            variable=self.ignore_all_blank_lines,
        ).pack(side="left", padx=6)

        ttk.Checkbutton(
            opts,
            text="Ignore extra whitespace inside lines",
            variable=self.ignore_extra_whitespace,
        ).pack(side="left", padx=6)

        ttk.Checkbutton(
            opts,
            text="Only show differences",
            variable=self.show_only_differences,
        ).pack(side="left", padx=6)

        self.status = ttk.Label(opts, textvariable=self.status_text)
        self.status.pack(side="right")

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=4)

        self.left_lines, self.left_text = self._make_text_pane(panes, "LEFT: Original / Expected")
        self.right_lines, self.right_text = self._make_text_pane(panes, "RIGHT: Your Transcription")

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

        self.left_text.tag_config("diff", background="#fdecef")
        self.left_text.tag_config("active_diff", background="#f8d6dc")
        self.right_text.tag_config("diff", background="#e8f5ea")
        self.right_text.tag_config("active_diff", background="#d0ecd6")

        self._bind_editor_events(self.left_text, self.left_lines)
        self._bind_editor_events(self.right_text, self.right_lines)
        self._refresh_line_numbers()

    def _make_text_pane(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=4)
        parent.add(frame, weight=1)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True)

        line_numbers = tk.Text(
            body,
            width=6,
            padx=4,
            takefocus=0,
            borderwidth=0,
            background="#f3f3f3",
            foreground="#666666",
            state="disabled",
            wrap="none",
            font=("Consolas", 10),
        )
        line_numbers.pack(side="left", fill="y")

        text = tk.Text(body, wrap="none", font=("Consolas", 10), undo=True)
        text.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(body, orient="vertical")
        yscroll.pack(side="right", fill="y")
        yscroll.configure(command=lambda *args, t=text, l=line_numbers: self._sync_text_and_lines(t, l, *args))
        text.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        xscroll.pack(fill="x")
        text.configure(xscrollcommand=xscroll.set)

        return line_numbers, text

    def _bind_editor_events(self, text_widget, line_widget):
        text_widget.bind("<KeyRelease>", lambda _event: self._refresh_line_numbers())
        text_widget.bind("<MouseWheel>", lambda _event: self.root.after_idle(self._refresh_line_numbers))
        text_widget.bind("<ButtonRelease-1>", lambda _event: self.root.after_idle(self._refresh_line_numbers))
        text_widget.bind("<Configure>", lambda _event: self.root.after_idle(self._refresh_line_numbers))
        line_widget.bind("<MouseWheel>", lambda _event: "break")
        line_widget.bind("<Button-1>", lambda _event: "break")

    def _set_line_numbers(self, line_widget, text_widget):
        content = text_widget.get("1.0", "end-1c")
        line_count = max(1, content.count("\n") + 1)
        line_text = "\n".join(f"{line:>4}" for line in range(1, line_count + 1))

        line_widget.configure(state="normal")
        line_widget.delete("1.0", tk.END)
        line_widget.insert("1.0", line_text)
        line_widget.configure(state="disabled")
        line_widget.yview_moveto(text_widget.yview()[0])

    def _refresh_line_numbers(self):
        self._set_line_numbers(self.left_lines, self.left_text)
        self._set_line_numbers(self.right_lines, self.right_text)

    def _sync_text_and_lines(self, text_widget, line_widget, *args):
        text_widget.yview(*args)
        line_widget.yview_moveto(text_widget.yview()[0])

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
        except Exception as exc:
            messagebox.showerror("File Error", f"Could not open file:\n{exc}")
            return

        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", data)
        self._refresh_line_numbers()

    def normalize_lines(self, text):
        lines = text.splitlines()

        normalized = []
        for original_line_number, line in enumerate(lines, start=1):
            normalized_line = line

            if self.ignore_whitespace_only_blank_lines.get() and normalized_line.strip() == "":
                normalized_line = ""

            if self.strip_trailing_spaces.get():
                normalized_line = normalized_line.rstrip()

            if self.ignore_extra_whitespace.get():
                normalized_line = " ".join(normalized_line.strip().split())

            normalized.append(
                {
                    "original_line_number": original_line_number,
                    "display_line": line,
                    "normalized_line": normalized_line,
                }
            )

        if self.ignore_all_blank_lines.get():
            normalized = [line for line in normalized if line["normalized_line"].strip() != ""]

        return normalized

    def compare(self):
        left_raw = self.left_text.get("1.0", "end-1c")
        right_raw = self.right_text.get("1.0", "end-1c")

        left_entries = self.normalize_lines(left_raw)
        right_entries = self.normalize_lines(right_raw)

        left = [entry["normalized_line"] for entry in left_entries]
        right = [entry["normalized_line"] for entry in right_entries]

        self.diff_text.delete("1.0", tk.END)
        self._clear_highlights()
        self.diff_blocks = []
        self.current_diff_index = -1
        self._set_jump_choices()

        if left == right:
            self.status_text.set("MATCH: no differences found.")
            self.diff_text.insert(tk.END, "No differences found.\n", "info")
            return

        self.status_text.set("Differences found.")

        matcher = difflib.SequenceMatcher(None, left, right)
        diff_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                if not self.show_only_differences.get():
                    for entry in left_entries[i1:i2]:
                        self.diff_text.insert(tk.END, f"  L{entry['original_line_number']:04d} | {entry['display_line']}\n", "same")
                continue

            diff_count += 1
            left_block = left_entries[i1:i2]
            right_block = right_entries[j1:j2]
            block = {
                "index": len(self.diff_blocks),
                "tag": tag,
                "left_entries": left_block,
                "right_entries": right_block,
                "left_range": self._format_line_range(left_block),
                "right_range": self._format_line_range(right_block),
                "report_start": None,
                "report_end": None,
            }
            self.diff_blocks.append(block)
            self._highlight_block(block, active=False)

            start_index = self.diff_text.index(tk.END)
            self.diff_text.insert(tk.END, f"\n--- Difference {diff_count}: {tag.upper()} ---\n", "info")
            self.diff_text.insert(
                tk.END,
                f"Lines: left {block['left_range']} | right {block['right_range']}\n",
                "warn",
            )

            if tag in ("replace", "delete"):
                self.diff_text.insert(tk.END, "Left/original:\n", "warn")
                for entry in left_block:
                    self.diff_text.insert(tk.END, f"- L{entry['original_line_number']:04d} | {entry['display_line']}\n", "left")

            if tag in ("replace", "insert"):
                self.diff_text.insert(tk.END, "Right/transcription:\n", "warn")
                for entry in right_block:
                    self.diff_text.insert(tk.END, f"+ R{entry['original_line_number']:04d} | {entry['display_line']}\n", "right")

            if tag == "replace":
                self._show_character_hint(left_block, right_block)

            end_index = self.diff_text.index(tk.END)
            block["report_start"] = start_index
            block["report_end"] = end_index

        self.diff_text.insert(tk.END, f"\nDone. Total difference blocks: {diff_count}\n", "info")
        self._set_jump_choices()
        self._select_diff(0)

    def _show_character_hint(self, left_entries, right_entries):
        max_pairs = min(len(left_entries), len(right_entries), 4)

        for n in range(max_pairs):
            a = left_entries[n]["display_line"]
            b = right_entries[n]["display_line"]

            if a == b:
                continue

            idx = 0
            limit = min(len(a), len(b))
            while idx < limit and a[idx] == b[idx]:
                idx += 1

            self.diff_text.insert(tk.END, f"  First character mismatch near column {idx + 1}\n", "info")
            self.diff_text.insert(tk.END, f"  Left : {a[max(0, idx - 30):idx + 50]}\n", "left")
            self.diff_text.insert(tk.END, f"  Right: {b[max(0, idx - 30):idx + 50]}\n", "right")

    def _highlight_block(self, block, active):
        tag = "active_diff" if active else "diff"

        for entry in block["left_entries"]:
            self.left_text.tag_add(tag, f"{entry['original_line_number']}.0", f"{entry['original_line_number']}.end+1c")

        for entry in block["right_entries"]:
            self.right_text.tag_add(tag, f"{entry['original_line_number']}.0", f"{entry['original_line_number']}.end+1c")

    def _clear_highlights(self):
        for widget in (self.left_text, self.right_text):
            widget.tag_remove("diff", "1.0", tk.END)
            widget.tag_remove("active_diff", "1.0", tk.END)


    def _set_jump_choices(self):
        if not self.diff_blocks:
            self.jump_combo["values"] = ("No differences",)
            self.jump_combo.current(0)
            self.jump_var.set("No differences")
            return

        values = [
            f"{index + 1}. {block['tag'].upper()} | L {block['left_range']} | R {block['right_range']}"
            for index, block in enumerate(self.diff_blocks)
        ]
        self.jump_combo["values"] = values
        self.jump_var.set(values[0] if self.current_diff_index in (-1, 0) else values[self.current_diff_index])

    def _on_jump_selected(self, _event):
        if not self.diff_blocks:
            return

        index = self.jump_combo.current()
        if index >= 0:
            self._select_diff(index)

    def _select_diff(self, index):
        if not (0 <= index < len(self.diff_blocks)):
            return

        self._clear_highlights()
        for block in self.diff_blocks:
            self._highlight_block(block, active=False)

        self.current_diff_index = index
        block = self.diff_blocks[index]
        self._highlight_block(block, active=True)

        target_left = self._line_for_jump(block["left_entries"], block["right_entries"])
        target_right = self._line_for_jump(block["right_entries"], block["left_entries"])

        self.left_text.see(f"{target_left}.0")
        self.right_text.see(f"{target_right}.0")

        if block["report_start"]:
            self.diff_text.see(block["report_start"])

        values = self.jump_combo["values"]
        if values:
            self.jump_combo.current(index)

        self.status_text.set(
            f"Problem {index + 1} of {len(self.diff_blocks)}: {block['tag'].upper()} at left {block['left_range']} and right {block['right_range']}."
        )

    def _line_for_jump(self, preferred_entries, fallback_entries):
        if preferred_entries:
            return preferred_entries[0]["original_line_number"]
        if fallback_entries:
            return fallback_entries[0]["original_line_number"]
        return 1

    def _format_line_range(self, entries):
        if not entries:
            return "-"

        start = entries[0]["original_line_number"]
        end = entries[-1]["original_line_number"]
        if start == end:
            return str(start)
        return f"{start}-{end}"

    def prev_difference(self):
        if not self.diff_blocks:
            return

        if self.current_diff_index <= 0:
            self._select_diff(len(self.diff_blocks) - 1)
        else:
            self._select_diff(self.current_diff_index - 1)

    def next_difference(self):
        if not self.diff_blocks:
            return

        if self.current_diff_index == -1 or self.current_diff_index >= len(self.diff_blocks) - 1:
            self._select_diff(0)
        else:
            self._select_diff(self.current_diff_index + 1)

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
        except Exception as exc:
            messagebox.showerror("Save Error", f"Could not save file:\n{exc}")
            return

        messagebox.showinfo("Saved", "Diff report saved.")

    def clear_all(self):
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)
        self.left_lines.configure(state="normal")
        self.left_lines.delete("1.0", tk.END)
        self.left_lines.configure(state="disabled")
        self.right_lines.configure(state="normal")
        self.right_lines.delete("1.0", tk.END)
        self.right_lines.configure(state="disabled")
        self.diff_text.delete("1.0", tk.END)
        self._clear_highlights()
        self.diff_blocks = []
        self.current_diff_index = -1
        self._set_jump_choices()
        self.status_text.set("Cleared.")
        self._refresh_line_numbers()


if __name__ == "__main__":
    root = tk.Tk()
    app = TextCompareApp(root)
    root.mainloop()
