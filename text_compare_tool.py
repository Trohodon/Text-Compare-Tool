import tkinter as tk
from tkinter import ttk, messagebox
import difflib


class TextCompareTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Text Compare Tool")
        self.root.geometry("1200x750")

        self.build_gui()

    def build_gui(self):
        title = ttk.Label(
            self.root,
            text="Text Compare Tool",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=10)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        left_frame = ttk.LabelFrame(main_frame, text="Original / Expected Text")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        right_frame = ttk.LabelFrame(main_frame, text="Your Transcription")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        self.left_text = tk.Text(left_frame, wrap="none", font=("Consolas", 11))
        self.left_text.pack(fill="both", expand=True)

        self.right_text = tk.Text(right_frame, wrap="none", font=("Consolas", 11))
        self.right_text.pack(fill="both", expand=True)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Compare Text", command=self.compare_text).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear Both", command=self.clear_text).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Copy Differences", command=self.copy_differences).pack(side="left", padx=5)

        self.status_label = ttk.Label(button_frame, text="Paste both versions, then click Compare Text.")
        self.status_label.pack(side="left", padx=20)

        result_frame = ttk.LabelFrame(self.root, text="Differences")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(result_frame, wrap="none", font=("Consolas", 10), height=14)
        self.result_text.pack(fill="both", expand=True)

        self.result_text.tag_config("added", foreground="green")
        self.result_text.tag_config("removed", foreground="red")
        self.result_text.tag_config("changed", foreground="blue")

    def compare_text(self):
        original = self.left_text.get("1.0", "end-1c").splitlines()
        transcription = self.right_text.get("1.0", "end-1c").splitlines()

        self.result_text.delete("1.0", tk.END)

        if original == transcription:
            self.status_label.config(text="✅ Text matches exactly.")
            self.result_text.insert(tk.END, "No differences found.\n")
            return

        self.status_label.config(text="❌ Differences found.")

        diff = difflib.ndiff(original, transcription)

        for line in diff:
            if line.startswith("- "):
                self.result_text.insert(tk.END, line + "\n", "removed")
            elif line.startswith("+ "):
                self.result_text.insert(tk.END, line + "\n", "added")
            elif line.startswith("? "):
                self.result_text.insert(tk.END, line + "\n", "changed")
            else:
                self.result_text.insert(tk.END, line + "\n")

    def clear_text(self):
        self.left_text.delete("1.0", tk.END)
        self.right_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.status_label.config(text="Cleared.")

    def copy_differences(self):
        differences = self.result_text.get("1.0", "end-1c")

        if not differences.strip():
            messagebox.showinfo("Nothing to Copy", "There are no differences to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(differences)
        self.status_label.config(text="Differences copied to clipboard.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TextCompareTool(root)
    root.mainloop()