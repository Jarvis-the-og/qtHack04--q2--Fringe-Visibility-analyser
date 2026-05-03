"""
Fringe Visibility Analyzer — Launcher
"""

import sys, ctypes
if sys.platform == "win32":
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, sys, os

# ─────────────────────────────────────────────────────────────────────────────
# Design tokens
# ─────────────────────────────────────────────────────────────────────────────

COLOR = {
    "bg":       "#0b0d17",
    "surface":  "#111420",
    "border":   "#1e2236",
    "muted":    "#1c2030",
    "accent":   "#00d4ff",
    "text":     "#dde4f0",
    "subtext":  "#6b728c",
}

# Accent color per module (index-aligned with MODULES list below)
MODULE_ACCENTS = ["#00d4ff", "#7df9ff", "#c8ff5c"]

FONT = "Courier"

# Spacing scale (pixels)
SP = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48}

# Layout
CONTENT_MAX_W = 980   # content column never wider than this
CONTENT_PAD_X = SP[7] # left/right padding inside the content column

# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────

MODULES = [
    {
        "number": "01",
        "title":  "Two Beams Variation",
        "desc": (
            "Adjust individual beam intensities I₁ and I₂, phase offset Δφ, and "
            "spatial frequency k. Beam profiles and the combined interference pattern "
            "update in real time."
        ),
        "file": "two_beams_variation.py",
    },
    {
        "number": "02",
        "title":  "Fringe Pattern Simulator",
        "desc": (
            "Full Young's double-slit geometry. Control wavelength λ, slit separation d, "
            "screen distance L, coherence γ, and tilt angle θ. Renders a live 2-D fringe "
            "pattern."
        ),
        "file": "fringe_pattern.py",
    },
    {
        "number": "03",
        "title":  "Visibility vs Intensity Ratio",
        "desc": (
            "Plots the analytic curve V = 2√r / (1+r). A live marker tracks the current "
            "I₁/I₂ ratio alongside a phasor diagram and a 2-D visibility heat-map over "
            "(I₁, I₂) space."
        ),
        "file": "visibility_vs_intensity.py",
    },
]

THEORY = [
    {
        "heading": "What is Fringe Visibility?",
        "body": (
            "Fringe visibility (also called fringe contrast) quantifies how clearly the "
            "bright and dark bands of an interference pattern can be distinguished.\n"
            "Michelson defined it as:\n\n"
            "        V  =  ( I_max − I_min ) / ( I_max + I_min )\n\n"
            "V = 1  →  perfect contrast; complete darkness between bright fringes.\n"
            "V = 0  →  no fringes detectable; uniform illumination.\n\n"
            "Visibility is governed by three independent factors: temporal coherence "
            "(path-length difference vs. coherence length), spatial coherence (finite "
            "source size), and intensity balance between the two interfering beams."
        ),
    },
    {
        "heading": "Effect of Unequal Beam Intensities",
        "body": (
            "For two beams with intensities I₁ and I₂, assuming perfect coherence, the "
            "maximum achievable visibility is:\n\n"
            "        V  =  2√(I₁ · I₂) / ( I₁ + I₂ )\n\n"
            "This is the geometric-mean–to–arithmetic-mean ratio of the amplitudes.\n"
            "When I₁ = I₂ the formula gives V = 1. Any imbalance strictly reduces "
            "contrast — a 4:1 intensity ratio already drops V to 0.8. The three "
            "simulation modules let you explore this relationship from complementary "
            "perspectives: waveform superposition, 2-D spatial pattern, and analytic "
            "curve with heat-map."
        ),
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def label(parent, text, size=9, weight="normal", color="text", **kw):
    """Shorthand for a consistently styled tk.Label."""
    return tk.Label(
        parent, text=text,
        font=(FONT, size, weight),
        fg=COLOR[color], bg=parent["bg"],
        **kw,
    )

def rule(parent, padx=0):
    """A 1-px horizontal separator."""
    f = tk.Frame(parent, bg=COLOR["border"], height=1)
    f.pack(fill="x", padx=padx)
    return f

# ─────────────────────────────────────────────────────────────────────────────
# Compound widgets
# ─────────────────────────────────────────────────────────────────────────────

class SectionHeading(tk.Frame):
    """
    A small all-caps label followed by a full-width rule.
    Used to introduce each section of the page.
    """
    def __init__(self, parent, text):
        super().__init__(parent, bg=COLOR["bg"])
        label(self, text, size=7, weight="bold", color="subtext").pack(
            anchor="w", pady=(0, SP[2])
        )
        tk.Frame(self, bg=COLOR["border"], height=1).pack(fill="x")


class TheoryBlock(tk.Frame):
    """
    A single theory/background entry: heading + body text.
    Left edge carries a 2 px accent bar.
    """
    def __init__(self, parent, heading, body):
        super().__init__(parent, bg=COLOR["surface"])
        # accent bar
        tk.Frame(self, bg=COLOR["accent"], width=2).pack(
            side="left", fill="y", padx=(0, SP[4])
        )
        # text column
        col = tk.Frame(self, bg=COLOR["surface"])
        col.pack(side="left", fill="both", expand=True,
                 pady=SP[4], padx=(0, SP[4]))

        label(col, heading.upper(), size=8, weight="bold", color="text").pack(anchor="w")
        tk.Frame(col, bg=COLOR["border"], height=1).pack(fill="x", pady=(SP[2], SP[3]))
        self._body = label(col, body, size=9, color="subtext",
                           justify="left", wraplength=600)
        self._body.pack(anchor="w")

    def reflow(self, available_width):
        self._body.config(wraplength=max(200, available_width - SP[5]))


class ModuleRow(tk.Frame):
    """
    One simulation module: number badge, title, description, launch button.
    Laid out as a single horizontal row with grid for alignment.
    """
    def __init__(self, parent, module, accent, on_launch):
        super().__init__(parent, bg=COLOR["surface"])

        # Top accent stripe
        tk.Frame(self, bg=accent, height=2).grid(
            row=0, column=0, columnspan=4, sticky="ew"
        )

        # ── Number badge ─────────────────────────────────────────────────────
        badge = tk.Frame(self, bg=COLOR["surface"], width=SP[7])
        badge.grid(row=1, column=0, sticky="ns", padx=(SP[4], 0), pady=SP[4])
        badge.grid_propagate(False)
        label(badge, module["number"], size=18, weight="bold",
              color="border").pack(anchor="center", expand=True)

        # ── Vertical divider ─────────────────────────────────────────────────
        tk.Frame(self, bg=COLOR["border"], width=1).grid(
            row=1, column=1, sticky="ns", padx=SP[4], pady=SP[3]
        )

        # ── Text column ──────────────────────────────────────────────────────
        text_col = tk.Frame(self, bg=COLOR["surface"])
        text_col.grid(row=1, column=2, sticky="nsew", pady=SP[4])

        label(text_col, f"MODULE {module['number']}",
              size=7, weight="bold", color="subtext").pack(anchor="w")
        label(text_col, module["title"],
              size=11, weight="bold", color="text").pack(anchor="w", pady=(SP[1], 0))
        self._desc = label(text_col, module["desc"],
                           size=9, color="subtext",
                           justify="left", wraplength=520)
        self._desc.pack(anchor="w", pady=(SP[2], 0))

        # ── Launch button ─────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=COLOR["surface"])
        btn_frame.grid(row=1, column=3, sticky="e",
                       padx=(SP[4], SP[4]), pady=SP[4])

        btn = tk.Button(
            btn_frame, text="Launch  ▶",
            font=(FONT, 8, "bold"),
            fg=COLOR["bg"], bg=accent,
            relief="flat", bd=0,
            padx=SP[4], pady=SP[3],
            cursor="hand2",
            command=lambda: on_launch(module["file"]),
        )
        btn.pack()
        btn.bind("<Enter>", lambda e: btn.config(bg="#ffffff", fg=accent))
        btn.bind("<Leave>", lambda e: btn.config(bg=accent, fg=COLOR["bg"]))

        # Status dot
        self._dot = tk.Label(
            btn_frame, text="●",
            font=(FONT, 10), fg=COLOR["border"], bg=COLOR["surface"]
        )
        self._dot.pack(pady=(4, 0))

        # Column weight: text column stretches
        self.grid_columnconfigure(2, weight=1)

    def set_status(self, status):
        """Update the status dot: 'idle', 'running', 'done'."""
        colors = {"idle": COLOR["border"], "running": "#44ff88", "done": "#ff5555"}
        self._dot.config(fg=colors.get(status, COLOR["border"]))

    def reflow(self, available_width):
        self._desc.config(wraplength=max(200, available_width - 250))


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────

class Launcher(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Fringe Visibility Analyzer  ·  Launcher")
        self.configure(bg=COLOR["bg"])
        self.resizable(True, True)
        self._proc_map: dict[str, subprocess.Popen] = {}   # file → process

        self._theory_blocks: list[TheoryBlock] = []
        self._module_rows:   list[ModuleRow]   = []

        self._maximise()
        self._apply_scrollbar_style()
        self._build_chrome()
        self._populate()

        self.bind("<F11>",     self._toggle_fullscreen)
        self.bind("<Escape>",  self._exit_fullscreen)
        self.bind("<Configure>", self._on_window_resize)
        self._poll_processes()


    # ── Initialisation helpers ────────────────────────────────────────────────

    def _maximise(self):
        for attempt in (
            lambda: self.state("zoomed"),
            lambda: self.attributes("-zoomed", True),
            lambda: self.geometry("1280x800"),
        ):
            try:
                attempt()
                return
            except tk.TclError:
                continue

    def _apply_scrollbar_style(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Dark.Vertical.TScrollbar",
            background=COLOR["muted"],
            troughcolor=COLOR["bg"],
            bordercolor=COLOR["bg"],
            arrowcolor=COLOR["border"],
            relief="flat",
        )

    # ── Chrome: canvas + scrollbar ────────────────────────────────────────────

    def _build_chrome(self):
        self._vsb = ttk.Scrollbar(self, orient="vertical",
                                   style="Dark.Vertical.TScrollbar")
        self._canvas = tk.Canvas(self, bg=COLOR["bg"],
                                  highlightthickness=0,
                                  yscrollcommand=self._vsb.set)
        self._vsb.configure(command=self._canvas.yview)

        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        for seq, delta in (("<MouseWheel>", None), ("<Button-4>", -1), ("<Button-5>", 1)):
            self._canvas.bind(seq, self._make_scroll_handler(delta))

        self._page = tk.Frame(self._canvas, bg=COLOR["bg"])
        self._page_id = self._canvas.create_window(
            (0, 0), window=self._page, anchor="nw"
        )
        self._page.bind("<Configure>",
                        lambda e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")
                        ))

    def _make_scroll_handler(self, fixed_delta):
        if fixed_delta is None:
            return lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units")
        return lambda e: self._canvas.yview_scroll(fixed_delta, "units")

    # ── Page content ──────────────────────────────────────────────────────────

    def _populate(self):
        p = self._page

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(p, bg=COLOR["bg"])
        hdr.pack(fill="x", padx=CONTENT_PAD_X, pady=(SP[7], 0))

        label(hdr, "Fringe Visibility Analyzer",
              size=22, weight="bold", color="accent").pack(anchor="w")
        label(hdr,
              "An interactive suite for exploring how beam intensity, coherence, and "
              "geometry govern fringe contrast in two-beam interference experiments.",
              size=9, color="subtext", justify="left", wraplength=700,
              ).pack(anchor="w", pady=(SP[2], 0))

        rule(p, padx=CONTENT_PAD_X)

        # ── Theory section ─────────────────────────────────────────────────────
        self._pack_section(p, "BACKGROUND")

        for entry in THEORY:
            blk = TheoryBlock(p, entry["heading"], entry["body"])
            blk.pack(fill="x", padx=CONTENT_PAD_X, pady=(0, SP[3]))
            self._theory_blocks.append(blk)

        rule(p, padx=CONTENT_PAD_X)

        # ── Modules section ────────────────────────────────────────────────────
        self._pack_section(p, "SIMULATION MODULES")

        for module, accent in zip(MODULES, MODULE_ACCENTS):
            row = ModuleRow(p, module, accent, self._launch)
            row.pack(fill="x", padx=CONTENT_PAD_X, pady=(0, SP[3]))
            self._module_rows.append(row)

        # ── Footer ─────────────────────────────────────────────────────────────
        rule(p, padx=CONTENT_PAD_X)
        foot = tk.Frame(p, bg=COLOR["bg"])
        foot.pack(fill="x", padx=CONTENT_PAD_X,
                  pady=(SP[3], SP[7]))
        label(foot,
              "Each module opens in a separate window and can run concurrently."
              "    F11 — toggle full screen    Esc — exit full screen",
              size=8, color="subtext").pack(side="left")
        label(foot, "v1.0", size=8, color="border").pack(side="right")

    def _pack_section(self, parent, title):
        tk.Frame(parent, bg=COLOR["bg"], height=SP[5]).pack()
        SectionHeading(parent, title).pack(
            fill="x", padx=CONTENT_PAD_X, pady=(0, SP[3])
        )

    # ── Responsive reflow ──────────────────────────────────────────────────────

    def _on_window_resize(self, event):
        if event.widget is not self:
            return
        w = event.width

        # Centre and clamp the content column
        col_w    = min(w, CONTENT_MAX_W)
        x_offset = max(0, (w - col_w) // 2)
        self._canvas.itemconfigure(self._page_id, width=col_w)
        self._canvas.coords(self._page_id, x_offset, 0)

        # Reflow wrapping in text-heavy widgets
        inner_w = col_w - CONTENT_PAD_X * 2
        for blk in self._theory_blocks:
            blk.reflow(inner_w)
        for row in self._module_rows:
            row.reflow(inner_w)

    # ── Full-screen ────────────────────────────────────────────────────────────

    def _toggle_fullscreen(self, _event=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _exit_fullscreen(self, _event=None):
        self.attributes("-fullscreen", False)

    # ── Subprocess launch ──────────────────────────────────────────────────────

    def _launch(self, filename):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, filename)
        if not os.path.exists(path):
            messagebox.showerror("File not found", f"Could not find:\n{path}")
            return
        proc = subprocess.Popen([sys.executable, path])
        self._proc_map[filename] = proc
        # find the matching ModuleRow and mark running
        for mod, row in zip(MODULES, self._module_rows):
            if mod["file"] == filename:
                row.set_status("running")

    def _poll_processes(self):
        """Check every 1 s if launched modules are still alive."""
        for filename, proc in list(self._proc_map.items()):
            ret = proc.poll()
            for mod, row in zip(MODULES, self._module_rows):
                if mod["file"] == filename:
                    if ret is None:
                        row.set_status("running")
                    else:
                        row.set_status("done")
        self.after(1000, self._poll_processes)



# ─────────────────────────────────────────────────────────────────────────────

def main():
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()