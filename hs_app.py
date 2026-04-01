"""
TJ HubPush — Windows desktop application
Transaction Junction HubSpot Push Tool
"""
import tkinter as tk

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY        = "#0f2744"
NAVY_HOVER  = "#1a3a5c"
NAVY_LOGO   = "#1565c0"
WHITE       = "#ffffff"
SIDEBAR_BG  = "#f4f6fa"
DETAIL_HDR  = "#eaecf0"
BORDER      = "#d0d4de"
TEXT        = "#1a1a2e"
TEXT_MUTED  = "#8a8fa8"

C_BLACK     = "#111111"
C_GREEN     = "#00a651"
C_ORANGE    = "#f5a623"
C_CYAN      = "#00b4d8"

FONT        = "Segoe UI"


# ── App ───────────────────────────────────────────────────────────────────────
class HubPushApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TJ HubPush")
        self.geometry("1080x560")
        self.minsize(820, 420)
        self.configure(bg=WHITE)
        self.resizable(True, True)

        # Try to apply a simple taskbar icon via a coloured placeholder
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._build_toolbar()
        self._build_body()
        self._show_placeholder()

    # ── Toolbar ───────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=NAVY, height=52)
        bar.pack(fill=tk.X, side=tk.TOP)
        bar.pack_propagate(False)

        # Logo tile
        logo_tile = tk.Frame(bar, bg=NAVY_LOGO, width=56, height=52)
        logo_tile.pack(side=tk.LEFT, fill=tk.Y)
        logo_tile.pack_propagate(False)
        tk.Label(
            logo_tile, text="TJ", bg=NAVY_LOGO, fg=WHITE,
            font=(FONT, 15, "bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # App name
        tk.Label(
            bar, text="TJ HubPush", bg=NAVY, fg=WHITE,
            font=(FONT, 11, "bold"), padx=14,
        ).pack(side=tk.LEFT, fill=tk.Y)

        # Thin vertical divider before buttons
        tk.Frame(bar, bg=NAVY_HOVER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, pady=10, padx=4
        )

        # Toolbar buttons — icons use clean Unicode glyphs
        btn_defs = [
            ("\u2315  Check for Documents", self._on_check_documents),
            ("\u2261  Review Summary",       self._on_review_summary),
            ("\u2191  Commit to HubSpot",    self._on_commit),
            ("\u29d6  View All Commits",     self._on_view_commits),
        ]
        self._toolbar_buttons = []
        for label, cmd in btn_defs:
            btn = tk.Button(
                bar, text=label, command=cmd,
                bg=NAVY, fg=WHITE,
                activebackground=NAVY_HOVER, activeforeground=WHITE,
                relief=tk.FLAT, bd=0,
                padx=18, pady=0,
                font=(FONT, 9),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, fill=tk.Y)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=NAVY_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=NAVY))
            self._toolbar_buttons.append(btn)

    # ── Body (sidebar + details) ──────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=WHITE)
        body.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = tk.Frame(body, bg=SIDEBAR_BG, width=292)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Sidebar header
        s_hdr = tk.Frame(sidebar, bg=NAVY, height=36)
        s_hdr.pack(fill=tk.X)
        s_hdr.pack_propagate(False)
        tk.Label(
            s_hdr, text="STATUS", bg=NAVY, fg=WHITE,
            font=(FONT, 8, "bold"), padx=18,
        ).pack(side=tk.LEFT, fill=tk.Y)

        # Stats
        self.stat_vars: dict[str, tk.StringVar] = {}
        stats_defs = [
            ("Total Restaurants",       "total",     C_BLACK),
            ("Total Pushed to HubSpot", "pushed",    C_GREEN),
            ("Total Remaining",         "remaining", C_ORANGE),
            ("Pushed in Last Commit",   "last",      C_CYAN),
        ]
        for label, key, colour in stats_defs:
            var = tk.StringVar(value="\u2014")
            self.stat_vars[key] = var
            row_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
            row_frame.pack(fill=tk.X)
            # bottom border
            tk.Frame(row_frame, bg=BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)
            inner = tk.Frame(row_frame, bg=SIDEBAR_BG, pady=16)
            inner.pack(fill=tk.X, padx=20)
            tk.Label(
                inner, text=label, bg=SIDEBAR_BG, fg=TEXT,
                font=(FONT, 9), anchor="w",
            ).pack(side=tk.LEFT)
            tk.Label(
                inner, textvariable=var, bg=SIDEBAR_BG, fg=colour,
                font=(FONT, 12, "bold"), anchor="e",
            ).pack(side=tk.RIGHT)

        # ── Vertical divider ──────────────────────────────────────────────────
        tk.Frame(body, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # ── Details panel ─────────────────────────────────────────────────────
        right = tk.Frame(body, bg=WHITE)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        d_hdr = tk.Frame(right, bg=DETAIL_HDR, height=36)
        d_hdr.pack(fill=tk.X)
        d_hdr.pack_propagate(False)
        self._detail_title_var = tk.StringVar(value="DETAILS")
        tk.Label(
            d_hdr, textvariable=self._detail_title_var,
            bg=DETAIL_HDR, fg=TEXT,
            font=(FONT, 8, "bold"), padx=18,
        ).pack(side=tk.LEFT, fill=tk.Y)

        self.detail_frame = tk.Frame(right, bg=WHITE)
        self.detail_frame.pack(fill=tk.BOTH, expand=True)

    # ── Detail panel helpers ──────────────────────────────────────────────────
    def _clear_details(self):
        for w in self.detail_frame.winfo_children():
            w.destroy()

    def _show_placeholder(self, message="Select an action from the toolbar to get started"):
        self._clear_details()
        self._detail_title_var.set("DETAILS")
        tk.Label(
            self.detail_frame, text=message,
            bg=WHITE, fg=TEXT_MUTED,
            font=(FONT, 10),
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _show_detail_table(self, title: str, rows: list[tuple], headers: list[str]):
        """Render a scrollable table in the details panel."""
        self._clear_details()
        self._detail_title_var.set(title)

        container = tk.Frame(self.detail_frame, bg=WHITE)
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Header row
        hdr_row = tk.Frame(container, bg=NAVY)
        hdr_row.pack(fill=tk.X)
        for col, h in enumerate(headers):
            tk.Label(
                hdr_row, text=h, bg=NAVY, fg=WHITE,
                font=(FONT, 8, "bold"),
                padx=10, pady=6, anchor="w",
                width=max(12, len(h) + 2),
            ).grid(row=0, column=col, sticky="ew", padx=1)

        # Scrollable body
        canvas = tk.Canvas(container, bg=WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=WHITE)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        even_bg = WHITE
        odd_bg  = "#f9fafc"
        for r_idx, row in enumerate(rows):
            row_bg = even_bg if r_idx % 2 == 0 else odd_bg
            for c_idx, cell in enumerate(row):
                cell_str = str(cell) if cell is not None else ""
                # Colour-code PASS/FAIL
                fg = TEXT
                if cell_str == "PASS":
                    fg = C_GREEN
                elif cell_str == "FAIL":
                    fg = "#c0392b"
                tk.Label(
                    scroll_frame, text=cell_str[:80],
                    bg=row_bg, fg=fg,
                    font=(FONT, 8),
                    padx=10, pady=5, anchor="w",
                    width=max(12, len(headers[c_idx]) + 2),
                ).grid(row=r_idx, column=c_idx, sticky="ew", padx=1, pady=0)
                tk.Frame(scroll_frame, bg=BORDER, height=1).grid(
                    row=r_idx, column=c_idx, sticky="sew", padx=1
                )

        # Mouse-wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _show_log(self, title: str, lines: list[str]):
        """Render a scrollable log output in the details panel."""
        self._clear_details()
        self._detail_title_var.set(title)

        frame = tk.Frame(self.detail_frame, bg=WHITE)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        text = tk.Text(
            frame, bg="#0d1117", fg="#e6edf3",
            font=("Consolas", 9), wrap=tk.WORD,
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED,
        )
        sb = tk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)

        text.tag_config("ok",    foreground=C_GREEN)
        text.tag_config("err",   foreground="#f85149")
        text.tag_config("warn",  foreground=C_ORANGE)
        text.tag_config("muted", foreground=TEXT_MUTED)

        text.config(state=tk.NORMAL)
        for line in lines:
            low = line.lower()
            if any(k in low for k in ("error", "fail", "http 4", "http 5", "abort")):
                tag = "err"
            elif any(k in low for k in ("skip", "warn", "already")):
                tag = "warn"
            elif any(k in low for k in ("created", "uploaded", "patched", "ok", "pass", "done")):
                tag = "ok"
            else:
                tag = "muted"
            text.insert(tk.END, line + "\n", tag)
        text.config(state=tk.DISABLED)
        text.see(tk.END)
        return text

    # ── Public stat setter ────────────────────────────────────────────────────
    def set_stats(self, total: int, pushed: int, remaining: int, last: int):
        self.stat_vars["total"].set(f"{total:,}")
        self.stat_vars["pushed"].set(f"{pushed:,}")
        self.stat_vars["remaining"].set(f"{remaining:,}")
        self.stat_vars["last"].set(f"{last:,}")

    # ── Button handlers (stubs — to be wired in next iteration) ──────────────
    def _on_check_documents(self):
        self._show_placeholder("Check for Documents — coming soon")

    def _on_review_summary(self):
        self._show_placeholder("Review Summary — coming soon")

    def _on_commit(self):
        self._show_placeholder("Commit to HubSpot — coming soon")

    def _on_view_commits(self):
        self._show_placeholder("View All Commits — coming soon")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = HubPushApp()
    app.mainloop()
