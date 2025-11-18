# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from run_all_combinations import run_all_combinations

class BuildPickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Build Picker (Numba backend)")
        self.root.geometry("980x640")

        self.json_path = tk.StringVar()
        tk.Label(root, text="Items JSON:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        tk.Entry(root, textvariable=self.json_path, width=70).grid(row=0, column=1, sticky="we", padx=6)
        tk.Button(root, text="Browse", command=self.browse).grid(row=0, column=2, padx=6)

        tk.Label(root, text="Required stats (e.g. str:50,dex:40):").grid(row=1, column=0, columnspan=3, sticky="w", padx=6)
        self.req_entry = tk.Entry(root, width=90)
        self.req_entry.grid(row=2, column=0, columnspan=3, padx=6, sticky="we")

        tk.Label(root, text="Top N results:").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.topn = tk.IntVar(value=10)
        tk.Entry(root, textvariable=self.topn, width=8).grid(row=3, column=1, sticky="w", padx=6)

        self.gpu_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Try GPU (requires cupy + custom GPU kernel - currently not implemented)", variable=self.gpu_var, state="disabled").grid(row=3, column=2, sticky="w")

        tk.Button(root, text="Find best", command=self.find).grid(row=4, column=0, columnspan=3, pady=8)

        # status
        self.status = tk.StringVar(value="Idle")
        tk.Label(root, textvariable=self.status).grid(row=5, column=0, columnspan=3, sticky="w", padx=6)

        # results frame
        frame = tk.Frame(root)
        frame.grid(row=6, column=0, columnspan=3, sticky="nsew")
        root.grid_rowconfigure(6, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.tree = ttk.Treeview(frame, columns=("combo", "stats"), show="headings")
        self.tree.heading("combo", text="Combination")
        self.tree.heading("stats", text="Required stats totals")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if p:
            self.json_path.set(p)

    def parse_required(self):
        txt = self.req_entry.get().strip()
        if not txt:
            return {}
        out = {}
        for pair in txt.split(","):
            if ":" not in pair:
                messagebox.showerror("Parse error", "Required stats syntax invalid. Use e.g. str:50,dex:40")
                return None
            k, v = pair.split(":", 1)
            try:
                out[k.strip()] = int(v.strip())
            except:
                messagebox.showerror("Parse error", f"Invalid number for {k.strip()}")
                return None
        return out

    def find(self):
        path = self.json_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select items.json first")
            return
        req = self.parse_required()
        if req is None:
            return
        topn = int(self.topn.get())

        self.status.set("Computing (this may take time for large files, Numba will JIT on first run)...")
        self.root.update_idletasks()

        try:
            results = run_all_combinations(path, req, topn, use_gpu=False)
        except Exception as e:
            messagebox.showerror("Error", f"Computation failed:\n{e}")
            self.status.set("Error")
            return

        # display
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for name, stats in results.items():
            stats_str = ", ".join(f"{k}:{v}" for k, v in stats.items())
            self.tree.insert("", "end", values=(name, stats_str))

        self.status.set(f"Done — {len(results)} results")

if __name__ == "__main__":
    root = tk.Tk()
    app = BuildPickerGUI(root)
    root.mainloop()
