"""
Simulation 1: Two Beams Variation
Demonstrates how unequal beam intensities affect the combined intensity profile
and fringe visibility in real time.

PATCHES APPLIED:
  - FIX 1 & 2: Removed spurious +pi/4 offset from Beam 2 formula.

IMPROVEMENTS v1.1:
  - ToolTip hover hints on every slider
  - Preset scenario buttons
  - Export plot (PNG / PDF / SVG)
  - Ctrl+R keyboard shortcut → reset
  - Live numerical formula substitution
  - 25 ms slider debounce
  - High-DPI awareness (Windows)
"""

import sys
import ctypes
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec

# ── Colour Palette ───────────────────────────────────────────────────────────
BG        = "#0d0f14"
PANEL     = "#13161e"
ACCENT1   = "#00d4ff"
ACCENT2   = "#ff6b35"
COMBINED  = "#b8ff6b"
TEXT      = "#e8ecf4"
SUBTEXT   = "#7a8099"
SLIDER_BG = "#1c2030"
HIGHLIGHT = "#252a3a"

matplotlib.rcParams.update({
    "axes.facecolor":   PANEL,
    "figure.facecolor": BG,
    "axes.edgecolor":   HIGHLIGHT,
    "axes.labelcolor":  TEXT,
    "xtick.color":      SUBTEXT,
    "ytick.color":      SUBTEXT,
    "text.color":       TEXT,
    "grid.color":       HIGHLIGHT,
    "grid.linewidth":   0.6,
    "font.family":      "monospace",
})

# ── Presets ──────────────────────────────────────────────────────────────────
PRESETS = [
    ("Equal Beams",   {"I1": 1.0,  "I2": 1.0,  "phi": 0.0,   "k": 4.0}),
    ("Phase 180°",    {"I1": 1.0,  "I2": 1.0,  "phi": 180.0, "k": 4.0}),
    ("4 : 1 Ratio",   {"I1": 2.0,  "I2": 0.5,  "phi": 0.0,   "k": 4.0}),
    ("High Freq",     {"I1": 1.0,  "I2": 1.0,  "phi": 0.0,   "k": 10.0}),
    ("Dim Beam 2",    {"I1": 1.5,  "I2": 0.1,  "phi": 45.0,  "k": 5.0}),
]

# ── Tooltip text ─────────────────────────────────────────────────────────────
TIPS = {
    "I₁  (Beam 1)": (
        "Intensity of Beam 1 (W).\n"
        "Equal I₁ and I₂ gives maximum visibility V = 1.\n"
        "Any imbalance strictly reduces contrast."
    ),
    "I₂  (Beam 2)": (
        "Intensity of Beam 2 (W).\n"
        "Try matching I₁ = I₂ for perfect fringes, then\n"
        "increase one to watch visibility drop."
    ),
    "Phase Δφ": (
        "Relative phase offset between beams (degrees).\n"
        "0° → constructive at centre (bright fringe).\n"
        "180° → destructive at centre (dark fringe).\n"
        "Slides the entire pattern left / right."
    ),
    "Freq  k": (
        "Spatial frequency of the pattern (rad / unit length).\n"
        "Higher k → more fringes packed into the window.\n"
        "Corresponds to closer slit spacing in a real DSE."
    ),
}


# ── ToolTip ──────────────────────────────────────────────────────────────────
class ToolTip:
    """Lightweight hover tooltip that follows the cursor to any Tk widget."""
    def __init__(self, widget, text):
        self._win = None
        widget.bind("<Enter>", lambda e: self._show(e, text))
        widget.bind("<Leave>", lambda e: self._hide())

    def _show(self, event, text):
        if self._win:
            return
        x = event.widget.winfo_rootx() + 24
        y = event.widget.winfo_rooty() + event.widget.winfo_height() + 6
        self._win = tw = tk.Toplevel(event.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg="#1a2035")
        tk.Frame(tw, bg=ACCENT1, height=1).pack(fill="x")
        tk.Label(
            tw, text=text,
            font=("Courier", 8), fg=TEXT, bg="#1a2035",
            padx=10, pady=7, wraplength=280, justify="left",
        ).pack()

    def _hide(self):
        if self._win:
            self._win.destroy()
            self._win = None


# ── Main App ─────────────────────────────────────────────────────────────────
class TwoBeamsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Two Beams Variation  ·  Fringe Visibility Analyzer")
        root.configure(bg=BG)
        root.geometry("1220x800")
        root.resizable(True, True)

        self.I1  = tk.DoubleVar(value=1.0)
        self.I2  = tk.DoubleVar(value=1.0)
        self.phi = tk.DoubleVar(value=0.0)
        self.k   = tk.DoubleVar(value=4.0)
        self._upd_id = None

        self._build_ui()
        self._update()

        root.bind("<Control-r>", lambda e: self._reset())
        root.bind("<Control-R>", lambda e: self._reset())

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG, pady=10)
        hdr.pack(fill="x", padx=20)
        tk.Label(hdr, text="TWO BEAMS VARIATION",
                 font=("Courier", 20, "bold"), fg=ACCENT1, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  interference intensity & fringe quality",
                 font=("Courier", 11), fg=SUBTEXT, bg=BG).pack(side="left", pady=6)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        ctrl = tk.Frame(main, bg=PANEL, relief="flat", bd=0, width=306)
        ctrl.pack(side="left", fill="y", padx=(0, 12))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side="left", fill="both", expand=True)
        self._build_canvas(canvas_frame)

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(16, 4))
        tk.Label(f, text=text, font=("Courier", 9, "bold"),
                 fg=ACCENT1, bg=PANEL).pack(side="left")
        tk.Frame(f, bg=HIGHLIGHT, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0))

    def _slider(self, parent, label, var, lo, hi, color,
                res=0.01, fmt="{:.2f}", unit=""):
        row = tk.Frame(parent, bg=PANEL, pady=4)
        row.pack(fill="x", padx=14)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        lw = tk.Label(top, text=label, font=("Courier", 10),
                      fg=TEXT, bg=PANEL)
        lw.pack(side="left")
        vl = tk.Label(top, text=fmt.format(var.get()) + unit,
                      font=("Courier", 10, "bold"), fg=color,
                      bg=PANEL, width=8)
        vl.pack(side="right")

        sl = ttk.Scale(row, from_=lo, to=hi, variable=var,
                       orient="horizontal", length=250)
        sl.pack(fill="x")

        def on(*_):
            vl.config(text=fmt.format(var.get()) + unit)
            self._debounced_update()
        var.trace_add("write", on)

        trow = tk.Frame(row, bg=PANEL)
        trow.pack(fill="x")
        tk.Label(trow, text=f"{lo}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="left")
        tk.Label(trow, text=f"{hi}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale", background=PANEL,
                        troughcolor=SLIDER_BG, sliderthickness=14)
        if label in TIPS:
            ToolTip(lw, TIPS[label])

    def _build_controls(self, parent):
        tk.Label(parent, text="PARAMETERS",
                 font=("Courier", 12, "bold"), fg=TEXT, bg=PANEL).pack(pady=(20, 0))
        tk.Label(parent, text="adjust sliders to see live changes",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        self._section(parent, "BEAM INTENSITIES")
        self._slider(parent, "I₁  (Beam 1)", self.I1, 0.01, 2.0, ACCENT1, unit=" W")
        self._slider(parent, "I₂  (Beam 2)", self.I2, 0.01, 2.0, ACCENT2, unit=" W")

        self._section(parent, "WAVE PROPERTIES")
        self._slider(parent, "Phase Δφ", self.phi, 0, 360, COMBINED,
                     res=1, fmt="{:.0f}", unit="°")
        self._slider(parent, "Freq  k", self.k, 1.0, 12.0, "#d4aaff",
                     res=0.1, fmt="{:.1f}")

        # Live metrics
        self._section(parent, "LIVE METRICS")
        self.vis_var   = tk.StringVar(value="—")
        self.imax_var  = tk.StringVar(value="—")
        self.imin_var  = tk.StringVar(value="—")
        self.ratio_var = tk.StringVar(value="—")
        for lbl, var, col in [
            ("Visibility  V", self.vis_var,   COMBINED),
            ("I_max",         self.imax_var,  ACCENT1),
            ("I_min",         self.imin_var,  ACCENT2),
            ("I₁ / I₂",       self.ratio_var, "#d4aaff"),
        ]:
            row = tk.Frame(parent, bg=HIGHLIGHT, pady=6, padx=10)
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=lbl, font=("Courier", 9),
                     fg=SUBTEXT, bg=HIGHLIGHT).pack(side="left")
            tk.Label(row, textvariable=var, font=("Courier", 11, "bold"),
                     fg=col, bg=HIGHLIGHT).pack(side="right")

        # Live formula substitution
        fbox = tk.Frame(parent, bg="#0a1420", pady=10, padx=12)
        fbox.pack(fill="x", padx=14, pady=(14, 0))
        tk.Label(fbox, text="FORMULA  (live)",
                 font=("Courier", 7, "bold"), fg=ACCENT1, bg="#0a1420").pack(anchor="w")
        tk.Label(fbox, text="V = 2√(I₁·I₂) / (I₁+I₂)",
                 font=("Courier", 9), fg=TEXT, bg="#0a1420").pack(anchor="w", pady=(3, 1))
        self.fsub = tk.Label(fbox, text="",
                             font=("Courier", 8), fg=SUBTEXT, bg="#0a1420",
                             justify="left")
        self.fsub.pack(anchor="w")

        # Presets
        self._section(parent, "PRESETS")
        for name, vals in PRESETS:
            b = tk.Button(parent, text=name, font=("Courier", 8),
                          fg=TEXT, bg=HIGHLIGHT, relief="flat", bd=0,
                          pady=4, cursor="hand2",
                          command=lambda v=vals: self._apply_preset(v))
            b.pack(fill="x", padx=14, pady=2)
            b.bind("<Enter>", lambda e, w=b: w.config(bg=ACCENT1, fg=BG))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=HIGHLIGHT, fg=TEXT))

        # Actions
        self._section(parent, "ACTIONS")
        ar = tk.Frame(parent, bg=PANEL)
        ar.pack(fill="x", padx=14, pady=(2, 4))
        eb = tk.Button(ar, text="📷  EXPORT", font=("Courier", 8, "bold"),
                       fg=BG, bg="#d4aaff", relief="flat", bd=0,
                       pady=6, cursor="hand2", command=self._export)
        eb.pack(side="left", fill="x", expand=True, padx=(0, 4))
        rb = tk.Button(ar, text="⟳  RESET", font=("Courier", 8, "bold"),
                       fg=BG, bg=ACCENT1, relief="flat", bd=0,
                       pady=6, cursor="hand2", command=self._reset)
        rb.pack(side="left", fill="x", expand=True)
        tk.Label(parent, text="Ctrl+R  →  reset",
                 font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(pady=(0, 12))

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(9, 6.5), facecolor=BG, tight_layout=False)
        self.fig.subplots_adjust(hspace=0.42, left=0.09, right=0.97,
                                 top=0.93, bottom=0.08)
        gs = GridSpec(2, 2, figure=self.fig)
        self.ax_main  = self.fig.add_subplot(gs[0, :])
        self.ax_beam1 = self.fig.add_subplot(gs[1, 0])
        self.ax_beam2 = self.fig.add_subplot(gs[1, 1])
        for ax in (self.ax_main, self.ax_beam1, self.ax_beam2):
            ax.grid(True, linestyle="--", alpha=0.4)
            ax.set_facecolor(PANEL)
            for spine in ax.spines.values():
                spine.set_edgecolor(HIGHLIGHT)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Physics ──────────────────────────────────────────────────────────────
    def _compute(self):
        x   = np.linspace(0, 2 * np.pi, 1000)
        I1  = self.I1.get()
        I2  = self.I2.get()
        k   = self.k.get()
        phi = np.deg2rad(self.phi.get())
        I_combined = I1 + I2 + 2 * np.sqrt(I1 * I2) * np.cos(k * x + phi)
        I_beam1    = I1 * (1 + np.cos(k * x))
        I_beam2    = I2 * (1 + np.cos(k * x + phi))
        I_max = (np.sqrt(I1) + np.sqrt(I2)) ** 2
        I_min = (np.sqrt(I1) - np.sqrt(I2)) ** 2
        V     = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) > 0 else 0.0
        return x, I_beam1, I_beam2, I_combined, I_max, I_min, V

    # ── Debounce ─────────────────────────────────────────────────────────────
    def _debounced_update(self, *_):
        if self._upd_id is not None:
            try:
                self.root.after_cancel(self._upd_id)
            except Exception:
                pass
        self._upd_id = self.root.after(25, self._update)

    # ── Render ───────────────────────────────────────────────────────────────
    def _update(self, *_):
        self._upd_id = None
        x, ib1, ib2, icom, imax, imin, V = self._compute()
        I1, I2  = self.I1.get(), self.I2.get()
        phi_deg = self.phi.get()

        self.vis_var.set(f"{V:.4f}")
        self.imax_var.set(f"{imax:.3f}")
        self.imin_var.set(f"{imin:.3f}")
        self.ratio_var.set(f"{I1 / I2:.3f}")

        # Live formula substitution
        denom = I1 + I2
        num   = 2 * np.sqrt(I1 * I2)
        self.fsub.config(
            text=(f"= 2·√({I1:.2f}·{I2:.2f}) / ({denom:.2f})\n"
                  f"= {num:.4f} / {denom:.4f}\n"
                  f"= {V:.4f}")
        )

        # top: combined
        ax = self.ax_main
        ax.cla()
        ax.set_facecolor(PANEL)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.fill_between(x, icom, alpha=0.18, color=COMBINED)
        ax.plot(x, icom, color=COMBINED, lw=2.2, label="Combined I(x)")
        ax.axhline(imax, color=ACCENT1, lw=1.1, ls="--", label=f"I_max = {imax:.3f}")
        ax.axhline(imin, color=ACCENT2, lw=1.1, ls="--", label=f"I_min = {imin:.3f}")
        ax.set_title(f"Combined Intensity Pattern   |   Visibility V = {V:.4f}",
                     color=TEXT, fontsize=11, pad=8)
        ax.set_xlabel("Position  x  (rad)", fontsize=9)
        ax.set_ylabel("Intensity (a.u.)", fontsize=9)
        ax.legend(loc="upper right", fontsize=8,
                  facecolor=PANEL, edgecolor=HIGHLIGHT, labelcolor=TEXT)
        extent = [x[0], x[-1], 0, icom.max() * 1.05]
        ax.imshow(np.tile(np.cos(self.k.get() * x + np.deg2rad(phi_deg)), (30, 1)),
                  aspect="auto", extent=extent, alpha=0.06, cmap="bwr", origin="lower")
        ax.set_ylim(0, icom.max() * 1.12)
        for sp in ax.spines.values():
            sp.set_edgecolor(HIGHLIGHT)

        # bottom-left: beam 1
        ax1 = self.ax_beam1
        ax1.cla(); ax1.set_facecolor(PANEL)
        ax1.grid(True, linestyle="--", alpha=0.35)
        ax1.fill_between(x, ib1, alpha=0.15, color=ACCENT1)
        ax1.plot(x, ib1, color=ACCENT1, lw=1.8)
        ax1.set_title(f"Beam 1   I₁ = {I1:.2f} W", color=ACCENT1, fontsize=9)
        ax1.set_xlabel("Position  x", fontsize=8)
        ax1.set_ylabel("Intensity", fontsize=8)
        for sp in ax1.spines.values():
            sp.set_edgecolor(HIGHLIGHT)

        # bottom-right: beam 2
        ax2 = self.ax_beam2
        ax2.cla(); ax2.set_facecolor(PANEL)
        ax2.grid(True, linestyle="--", alpha=0.35)
        ax2.fill_between(x, ib2, alpha=0.15, color=ACCENT2)
        ax2.plot(x, ib2, color=ACCENT2, lw=1.8)
        ax2.set_title(f"Beam 2   I₂ = {I2:.2f} W", color=ACCENT2, fontsize=9)
        ax2.set_xlabel("Position  x", fontsize=8)
        ax2.set_ylabel("Intensity", fontsize=8)
        for sp in ax2.spines.values():
            sp.set_edgecolor(HIGHLIGHT)

        self.fig.subplots_adjust(hspace=0.48, left=0.09, right=0.97,
                                 top=0.93, bottom=0.08)
        self.canvas.draw_idle()

    # ── Actions ──────────────────────────────────────────────────────────────
    def _apply_preset(self, vals):
        self.I1.set(vals["I1"])
        self.I2.set(vals["I2"])
        self.phi.set(vals["phi"])
        self.k.set(vals["k"])

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Export plot",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"),
                       ("PDF document", "*.pdf"),
                       ("SVG vector", "*.svg")],
        )
        if path:
            self.fig.savefig(path, dpi=150, bbox_inches="tight",
                             facecolor=BG)

    def _reset(self):
        self.I1.set(1.0)
        self.I2.set(1.0)
        self.phi.set(0.0)
        self.k.set(4.0)


def main():
    root = tk.Tk()
    TwoBeamsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()