"""
TJ HubPush — Windows desktop application
Transaction Junction HubSpot Push Tool
"""
import os
import tkinter as tk
from tkinter import messagebox

from hubpush_core.auth_client import AuthClient, AuthConfig

# Load cloud config from environment (or cloud.env file if present)
_env_file = os.path.join(os.path.dirname(__file__), "cloud.env")
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

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


# ── Login Window ─────────────────────────────────────────────────────────────
class LoginWindow(tk.Tk):
    """
    Shown before the main app.  User picks their name from buttons, then
    types their 4-digit PIN.  On success the callback is called with the
    authenticated username.
    """

    def __init__(self, on_success):
        super().__init__()
        self._on_success = on_success
        self._selected_user: str | None = None
        self._user_buttons: dict[str, tk.Button] = {}

        self.title("TJ HubPush — Sign In")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.eval("tk::PlaceWindow . center")

        # Fetch usernames (shows fallback list if server unreachable)
        self._auth = AuthClient(AuthConfig.from_env())
        self._users = self._auth.get_users()

        self._build_ui()

    def _build_ui(self):
        # ── Header bar ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=NAVY, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        logo_tile = tk.Frame(header, bg=NAVY_LOGO, width=56, height=60)
        logo_tile.pack(side=tk.LEFT, fill=tk.Y)
        logo_tile.pack_propagate(False)
        tk.Label(
            logo_tile, text="TJ", bg=NAVY_LOGO, fg=WHITE,
            font=(FONT, 15, "bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            header, text="TJ HubPush", bg=NAVY, fg=WHITE,
            font=(FONT, 13, "bold"), padx=16,
        ).pack(side=tk.LEFT, fill=tk.Y)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=WHITE, padx=36, pady=28)
        body.pack(fill=tk.BOTH, expand=True)

        # Title
        tk.Label(
            body, text="Sign In", bg=WHITE, fg=TEXT,
            font=(FONT, 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            body, text="Select your name to continue", bg=WHITE, fg=TEXT_MUTED,
            font=(FONT, 9),
        ).pack(anchor="w", pady=(2, 20))

        # ── Username button grid ───────────────────────────────────────────────
        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill=tk.X, pady=(0, 24))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for idx, name in enumerate(self._users):
            row_idx, col_idx = divmod(idx, 2)
            btn = tk.Button(
                grid, text=name,
                bg=SIDEBAR_BG, fg=TEXT,
                activebackground=NAVY, activeforeground=WHITE,
                relief=tk.FLAT, bd=0,
                font=(FONT, 10),
                height=2,
                cursor="hand2",
                command=lambda n=name: self._select_user(n),
            )
            btn.grid(row=row_idx, column=col_idx, sticky="ew", padx=5, pady=4)
            self._user_buttons[name] = btn

        # ── Divider ───────────────────────────────────────────────────────────
        tk.Frame(body, bg=BORDER, height=1).pack(fill=tk.X, pady=(0, 20))

        # ── PIN section ───────────────────────────────────────────────────────
        self._selected_label_var = tk.StringVar(value="No name selected")
        tk.Label(
            body, textvariable=self._selected_label_var,
            bg=WHITE, fg=TEXT_MUTED,
            font=(FONT, 9, "italic"),
        ).pack(anchor="w", pady=(0, 6))

        pin_row = tk.Frame(body, bg=WHITE)
        pin_row.pack(fill=tk.X)

        tk.Label(
            pin_row, text="PIN", bg=WHITE, fg=TEXT,
            font=(FONT, 9, "bold"), width=4, anchor="w",
        ).pack(side=tk.LEFT)

        self._pin_var = tk.StringVar()
        self._pin_entry = tk.Entry(
            pin_row,
            textvariable=self._pin_var,
            show="●",
            font=(FONT, 14),
            width=8,
            relief=tk.FLAT,
            bd=0,
            bg=SIDEBAR_BG,
            fg=TEXT,
            insertbackground=TEXT,
        )
        self._pin_entry.pack(side=tk.LEFT, ipady=8, padx=(8, 0), fill=tk.X, expand=True)
        self._pin_entry.bind("<Return>", lambda _e: self._attempt_login())
        # Limit to 4 digits
        self._pin_var.trace_add("write", self._limit_pin)

        # ── Error label ───────────────────────────────────────────────────────
        self._error_var = tk.StringVar()
        self._error_label = tk.Label(
            body, textvariable=self._error_var,
            bg=WHITE, fg="#c0392b",
            font=(FONT, 9),
        )
        self._error_label.pack(anchor="w", pady=(10, 0))

        # ── Sign In button ────────────────────────────────────────────────────
        self._login_btn = tk.Button(
            body, text="Sign In  →",
            bg=NAVY, fg=WHITE,
            activebackground=NAVY_HOVER, activeforeground=WHITE,
            relief=tk.FLAT, bd=0,
            font=(FONT, 10, "bold"),
            padx=20, pady=10,
            cursor="hand2",
            command=self._attempt_login,
        )
        self._login_btn.pack(anchor="e", pady=(12, 0))

    def _select_user(self, name: str):
        """Highlight the clicked username button, deselect others."""
        self._selected_user = name
        self._selected_label_var.set(f"Signing in as: {name}")
        self._error_var.set("")
        for btn_name, btn in self._user_buttons.items():
            if btn_name == name:
                btn.config(bg=NAVY, fg=WHITE)
            else:
                btn.config(bg=SIDEBAR_BG, fg=TEXT)
        self._pin_var.set("")
        self._pin_entry.focus_set()

    def _limit_pin(self, *_args):
        """Keep PIN entry to 4 characters."""
        val = self._pin_var.get()
        digits = "".join(c for c in val if c.isdigit())
        if digits != val or len(val) > 4:
            self._pin_var.set(digits[:4])

    def _attempt_login(self):
        """Validate selection and PIN, then call cloud auth."""
        if not self._selected_user:
            self._error_var.set("Please select your name first.")
            return

        pin = self._pin_var.get().strip()
        if len(pin) != 4 or not pin.isdigit():
            self._error_var.set("Enter your 4-digit PIN.")
            return

        self._error_var.set("")
        self._login_btn.config(state=tk.DISABLED, text="Checking…")
        self.update_idletasks()

        ok, err = self._auth.login(self._selected_user, pin)

        if ok:
            username = self._selected_user
            self.destroy()
            self._on_success(username)
        else:
            self._error_var.set(err or "Invalid PIN. Please try again.")
            self._pin_var.set("")
            self._pin_entry.focus_set()
            self._login_btn.config(state=tk.NORMAL, text="Sign In  →")


# ── App ───────────────────────────────────────────────────────────────────────
class HubPushApp(tk.Tk):
    def __init__(self, username: str = ""):
        super().__init__()
        self._username = username
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

        # Logged-in user (right side)
        if self._username:
            tk.Label(
                bar, text=f"\u2022  {self._username}", bg=NAVY, fg=WHITE,
                font=(FONT, 9), padx=14,
            ).pack(side=tk.RIGHT, fill=tk.Y)

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
    def _launch(username: str):
        app = HubPushApp(username=username)
        app.mainloop()

    login = LoginWindow(on_success=_launch)
    login.mainloop()
