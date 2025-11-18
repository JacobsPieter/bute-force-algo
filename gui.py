# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from run_all_combinations import run_all_combinations
import threading

class BuildPickerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Build Picker (Numba backend)")

        tk.Label(root, text="Items JSON:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.json_var = tk.StringVar()
        tk.Entry(root, textvariable=self.json_var, width=60).grid(row=0, column=1, sticky="we", padx=6)
        tk.Button(root, text="Browse", command=self.browse).grid(row=0, column=2, padx=6)

        tk.Label(root, text="Min requirements (comma: key:val,...):").grid(row=1, column=0, columnspan=3, sticky="w", padx=6)
        self.min_entry = tk.Entry(root, width=90)
        self.min_entry.grid(row=2, column=0, columnspan=3, padx=6, pady=2)

        tk.Label(root, text="Maximize single stat (Mode A) e.g. sdRaw:").grid(row=3, column=0, sticky="w", padx=6)
        self.max_single = tk.Entry(root, width=20)
        self.max_single.grid(row=3, column=1, sticky="w")

        tk.Label(root, text="Maximize weights (Mode B) e.g. sdRaw:1.0,mdRaw:0.5").grid(row=4, column=0, columnspan=3, sticky="w", padx=6)
        self.weights_entry = tk.Entry(root, width=90)
        self.weights_entry.grid(row=5, column=0, columnspan=3, padx=6, pady=2)

        tk.Label(root, text="Top N:").grid(row=6, column=0, sticky="w", padx=6)
        self.topn = tk.IntVar(value=10)
        tk.Entry(root, textvariable=self.topn, width=8).grid(row=6, column=1, sticky="w")

        self.run_btn = tk.Button(root, text="Find builds", command=self.start_search)
        self.run_btn.grid(row=7, column=0, columnspan=3, pady=8)

        self.status = tk.StringVar(value="Idle")
        tk.Label(root, textvariable=self.status).grid(row=8, column=0, columnspan=3, sticky="w", padx=6)

        # results
        frame = tk.Frame(root)
        frame.grid(row=9, column=0, columnspan=3, sticky="nsew")
        root.grid_rowconfigure(9, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.tree = ttk.Treeview(frame, columns=("combo", "score"), show="headings")
        self.tree.heading("combo", text="Combination")
        self.tree.heading("score", text="Score")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if p:
            self.json_var.set(p)

    def parse_min_requirements(self, text: str):
        text = text.strip()
        if not text:
            return {}
        out = {}
        try:
            for pair in text.split(","):
                if not pair:
                    continue
                k, v = pair.split(":", 1)
                out[k.strip()] = int(v.strip())
        except Exception:
            return None
        return out

    def parse_weights(self, text: str):
        text = text.strip()
        if not text:
            return {}
        out = {}
        try:
            for pair in text.split(","):
                if not pair:
                    continue
                k, v = pair.split(":", 1)
                out[k.strip()] = float(v.strip())
        except Exception:
            return None
        return out

    def start_search(self):
        path = self.json_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Select items.json")
            return
        minreq = self.parse_min_requirements(self.min_entry.get())
        if minreq is None:
            messagebox.showerror("Error", "Invalid min requirements format")
            return
        weights = self.parse_weights(self.weights_entry.get())
        if weights is None:
            messagebox.showerror("Error", "Invalid weights format")
            return
        maximize = self.max_single.get().strip()
        topn = int(self.topn.get())

        # disable button while running
        self.run_btn.config(state="disabled")
        self.status.set("Computing (Numba JIT may compile on first run)...")
        self.tree.delete(*self.tree.get_children())

        # run in a thread to keep GUI responsive
        def worker():
            try:
                results = run_all_combinations(path, min_requirements=minreq, maximize=maximize, maximize_weights=weights, top_n=topn)
            except Exception as e:
                self.status.set("Error")
                messagebox.showerror("Error", f"Search failed:\n{e}")
                self.run_btn.config(state="normal")
                return
            # populate treeview (sorted by score desc)
            items = list(results.items())
            items.sort(key=lambda x: x[1].get("_score", 0.0), reverse=True)
            for name, info in items:
                score = info.get("_score", 0.0)
                self.tree.insert("", "end", values=(name, f"{score:.2f}"))
            self.status.set(f"Done - {len(items)} results")
            self.run_btn.config(state="normal")

        t = threading.Thread(target=worker, daemon=True)
        t.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = BuildPickerGUI(root)
    root.geometry("1000x700")
    root.mainloop()
