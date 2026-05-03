"""
Simulation 3: Visibility vs Intensity Ratio
Plots the analytic curve V = 2√r / (1 + r) where r = I1/I2.

PATCHES APPLIED:
  - FIX 1: Phasor label placement corrected (polar coordinates).
  - FIX 2: Window enlarged to 1440x860, GridSpec margins adjusted.
  - FIX 3: Colorbar stored in self._cbar to prevent accumulation.

IMPROVEMENTS v1.1:
  - ToolTip hover hints on every slider
  - Preset scenario buttons
  - Export plot (PNG / PDF / SVG)
  - Ctrl+R keyboard shortcut → reset
  - Live numerical formula substitution
  - Fixed Phase Δφ label to clarify phasor-only scope
  - 25 ms slider debounce
  - High-DPI awareness (Windows)
"""

import sys, ctypes
if sys.platform == "win32":
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0c0d14"
PANEL   = "#12141f"
ACCENT  = "#c8ff5c"
MKRCLR  = "#ff5c8a"
CYAN    = "#5ce0ff"
ORANGE  = "#ffa45c"
TEXT    = "#dfe5f5"
SUBTEXT = "#6b728c"
HI      = "#1d2133"
SLBG    = "#181c2d"

matplotlib.rcParams.update({
    "axes.facecolor": PANEL, "figure.facecolor": BG,
    "axes.edgecolor": HI, "axes.labelcolor": TEXT,
    "xtick.color": SUBTEXT, "ytick.color": SUBTEXT,
    "text.color": TEXT, "grid.color": HI,
    "grid.linewidth": 0.55, "font.family": "monospace",
})

PRESETS = [
    ("Perfect Balance",  {"I1": 1.0,  "I2": 1.0,  "phi": 0.0,  "zoom": 10.0}),
    ("4 : 1 Ratio",      {"I1": 2.0,  "I2": 0.5,  "phi": 0.0,  "zoom": 10.0}),
    ("9 : 1 Ratio",      {"I1": 4.5,  "I2": 0.5,  "phi": 0.0,  "zoom": 10.0}),
    ("Zoom Out (r=50)",  {"I1": 5.0,  "I2": 0.5,  "phi": 0.0,  "zoom": 50.0}),
    ("Phase 90°",        {"I1": 1.0,  "I2": 1.0,  "phi": 90.0, "zoom": 10.0}),
]

TIPS = {
    "I₁  (Beam 1)": (
        "Intensity of Beam 1 (W).\n"
        "Sets the numerator of the ratio r = I₁/I₂.\n"
        "Equal I₁=I₂ gives V=1 (perfect contrast)."
    ),
    "I₂  (Beam 2)": (
        "Intensity of Beam 2 (W).\n"
        "Sets the denominator of r = I₁/I₂.\n"
        "Increasing this while I₁ is fixed moves r toward 0."
    ),
    "Phase Δφ  (phasor only)": (
        "Phase offset between beams (degrees).\n"
        "Only affects the phasor diagram — does NOT change\n"
        "the V vs r curve or the heat-map."
    ),
    "X-axis max r": (
        "Upper limit of the r axis on the V vs r plot.\n"
        "Zoom in to r=2 to see the steep initial drop.\n"
        "Zoom out to r=50 to see the asymptotic approach to V=0."
    ),
}


class ToolTip:
    def __init__(self, widget, text):
        self._win = None
        widget.bind("<Enter>", lambda e: self._show(e, text))
        widget.bind("<Leave>", lambda e: self._hide())

    def _show(self, event, text):
        if self._win: return
        x = event.widget.winfo_rootx() + 24
        y = event.widget.winfo_rooty() + event.widget.winfo_height() + 6
        self._win = tw = tk.Toplevel(event.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg="#1a2035")
        tk.Frame(tw, bg=ACCENT, height=1).pack(fill="x")
        tk.Label(tw, text=text, font=("Courier", 8), fg=TEXT, bg="#1a2035",
                 padx=10, pady=7, wraplength=290, justify="left").pack()

    def _hide(self):
        if self._win: self._win.destroy(); self._win = None


class VisibilityRatioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Visibility vs Intensity Ratio  ·  Fringe Visibility Analyzer")
        root.configure(bg=BG)
        root.geometry("1460x880")
        root.resizable(True, True)

        self.I1   = tk.DoubleVar(value=1.0)
        self.I2   = tk.DoubleVar(value=1.0)
        self.phi  = tk.DoubleVar(value=0.0)
        self.zoom = tk.DoubleVar(value=10.0)
        self._cbar   = None
        self._upd_id = None

        self._build_ui()
        self._update()
        root.bind("<Control-r>", lambda e: self._reset())
        root.bind("<Control-R>", lambda e: self._reset())

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG, pady=8)
        hdr.pack(fill="x", padx=22)
        tk.Label(hdr, text="VISIBILITY  vs  INTENSITY RATIO",
                 font=("Courier", 18, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  V = 2√(I₁/I₂) / (1 + I₁/I₂)",
                 font=("Courier", 10), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)
        ab = tk.Frame(hdr, bg=BG)
        ab.pack(side="right")
        tk.Button(ab, text="📷 EXPORT", font=("Courier", 9, "bold"),
                  fg=BG, bg="#d4aaff", relief="flat", bd=0,
                  padx=10, pady=6, cursor="hand2",
                  command=self._export).pack(side="left", padx=(0, 6))
        tk.Button(ab, text="⟳  RESET", font=("Courier", 9, "bold"),
                  fg=BG, bg=ACCENT, relief="flat", bd=0,
                  padx=10, pady=6, cursor="hand2",
                  command=self._reset).pack(side="left", padx=(0, 4))

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        ctrl = tk.Frame(main, bg=PANEL, width=308)
        ctrl.pack(side="left", fill="y", padx=(0, 12))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_canvas(right)

    def _section(self, p, t):
        f = tk.Frame(p, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(16, 3))
        tk.Label(f, text=t, font=("Courier", 8, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Frame(f, bg=HI, height=1).pack(side="left", fill="x",
                                           expand=True, padx=(6, 0))

    def _slider(self, parent, label, var, lo, hi, color,
                res=0.01, fmt="{:.2f}", unit=""):
        row = tk.Frame(parent, bg=PANEL, pady=3)
        row.pack(fill="x", padx=14)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        lw = tk.Label(top, text=label, font=("Courier", 10), fg=TEXT, bg=PANEL)
        lw.pack(side="left")
        vl = tk.Label(top, text=fmt.format(var.get()) + unit,
                      font=("Courier", 10, "bold"), fg=color, bg=PANEL, width=9)
        vl.pack(side="right")
        sl = ttk.Scale(row, from_=lo, to=hi, variable=var,
                       orient="horizontal", length=258)
        sl.pack(fill="x")
        trow = tk.Frame(row, bg=PANEL)
        trow.pack(fill="x")
        tk.Label(trow, text=f"{lo}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="left")
        tk.Label(trow, text=f"{hi}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="right")

        def on(*_):
            vl.config(text=fmt.format(var.get()) + unit)
            self._debounced_update()
        var.trace_add("write", on)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale", background=PANEL,
                        troughcolor=SLBG, sliderthickness=14)
        if label in TIPS:
            ToolTip(lw, TIPS[label])

    def _build_controls(self, parent):
        tk.Label(parent, text="PARAMETERS",
                 font=("Courier", 12, "bold"), fg=TEXT, bg=PANEL).pack(pady=(18, 0))
        tk.Label(parent, text="move sliders — watch the marker",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        self._section(parent, "BEAM INTENSITIES")
        self._slider(parent, "I₁  (Beam 1)", self.I1, 0.01, 5.0, CYAN, unit=" W")
        self._slider(parent, "I₂  (Beam 2)", self.I2, 0.01, 5.0, ORANGE, unit=" W")

        self._section(parent, "DISPLAY")
        self._slider(parent, "Phase Δφ  (phasor only)", self.phi,
                     0, 360, "#d4aaff", res=1, fmt="{:.0f}", unit="°")
        self._slider(parent, "X-axis max r", self.zoom,
                     2.0, 50.0, ACCENT, res=0.5, fmt="{:.1f}")

        self._section(parent, "LIVE METRICS")
        self.m_ratio = tk.StringVar(value="—")
        self.m_vis   = tk.StringVar(value="—")
        self.m_imax  = tk.StringVar(value="—")
        self.m_imin  = tk.StringVar(value="—")
        self.m_cont  = tk.StringVar(value="—")
        for lbl, var, col in [
            ("I₁ / I₂  ratio r", self.m_ratio, ACCENT),
            ("Visibility  V",     self.m_vis,   MKRCLR),
            ("I_max",             self.m_imax,  CYAN),
            ("I_min",             self.m_imin,  ORANGE),
            ("Contrast  C",       self.m_cont,  "#d4aaff"),
        ]:
            row = tk.Frame(parent, bg=HI, pady=5, padx=10)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=lbl, font=("Courier", 9),
                     fg=SUBTEXT, bg=HI).pack(side="left")
            tk.Label(row, textvariable=var, font=("Courier", 11, "bold"),
                     fg=col, bg=HI).pack(side="right")

        # Quality badge
        self.quality_var = tk.StringVar(value="EXCELLENT")
        qbox = tk.Frame(parent, bg=HI, pady=10)
        qbox.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(qbox, text="FRINGE QUALITY", font=("Courier", 8),
                 fg=SUBTEXT, bg=HI).pack()
        self.q_lbl = tk.Label(qbox, textvariable=self.quality_var,
                              font=("Courier", 14, "bold"), fg=ACCENT, bg=HI)
        self.q_lbl.pack()

        # Live formula substitution
        fb = tk.Frame(parent, bg="#08101c", pady=8, padx=10)
        fb.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(fb, text="FORMULA  (live)", font=("Courier", 7, "bold"),
                 fg=ACCENT, bg="#08101c").pack(anchor="w")
        tk.Label(fb, text="V = 2√r / (1 + r)",
                 font=("Courier", 9), fg=TEXT, bg="#08101c").pack(anchor="w", pady=(2, 1))
        self.fsub = tk.Label(fb, text="", font=("Courier", 8),
                             fg=SUBTEXT, bg="#08101c", justify="left")
        self.fsub.pack(anchor="w")

        # Presets
        self._section(parent, "PRESETS")
        for name, vals in PRESETS:
            b = tk.Button(parent, text=name, font=("Courier", 8),
                          fg=TEXT, bg=HI, relief="flat", bd=0,
                          pady=3, cursor="hand2",
                          command=lambda v=vals: self._apply_preset(v))
            b.pack(fill="x", padx=14, pady=1)
            b.bind("<Enter>", lambda e, w=b: w.config(bg=ACCENT, fg=BG))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=HI, fg=TEXT))

        tk.Label(parent, text="Ctrl+R → reset",
                 font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(pady=(6, 10))

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(10.5, 8.0), facecolor=BG)
        gs = GridSpec(2, 2, figure=self.fig, hspace=0.48, wspace=0.42,
                      left=0.07, right=0.96, top=0.93, bottom=0.09)
        self.ax_main    = self.fig.add_subplot(gs[0, :])
        self.ax_phasor  = self.fig.add_subplot(gs[1, 0], projection="polar")
        self.ax_heatmap = self.fig.add_subplot(gs[1, 1])
        for ax in (self.ax_main, self.ax_heatmap):
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values(): sp.set_edgecolor(HI)
        self.ax_phasor.set_facecolor(PANEL)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _vis_from_ratio(self, r):
        return 2 * np.sqrt(r) / (1 + r)

    def _compute(self):
        I1   = self.I1.get(); I2 = self.I2.get()
        phi  = np.deg2rad(self.phi.get())
        r    = I1 / I2
        V    = self._vis_from_ratio(r)
        Imax = (np.sqrt(I1) + np.sqrt(I2))**2
        Imin = (np.sqrt(I1) - np.sqrt(I2))**2
        r_arr = np.linspace(0.001, self.zoom.get(), 2000)
        V_arr = self._vis_from_ratio(r_arr)
        return r_arr, V_arr, r, V, Imax, Imin, V, phi

    def _quality_label(self, V):
        if V >= 0.90: return "EXCELLENT", ACCENT
        if V >= 0.70: return "GOOD",      CYAN
        if V >= 0.40: return "MODERATE",  ORANGE
        return "POOR", MKRCLR

    def _debounced_update(self, *_):
        if self._upd_id is not None:
            try: self.root.after_cancel(self._upd_id)
            except Exception: pass
        self._upd_id = self.root.after(25, self._update)

    def _update(self, *_):
        self._upd_id = None
        r_arr, V_arr, r, V, Imax, Imin, C, phi = self._compute()

        self.m_ratio.set(f"{r:.4f}")
        self.m_vis.set(f"{V:.4f}")
        self.m_imax.set(f"{Imax:.3f}")
        self.m_imin.set(f"{Imin:.3f}")
        self.m_cont.set(f"{C:.4f}")
        qlbl, qcol = self._quality_label(V)
        self.quality_var.set(qlbl)
        self.q_lbl.config(fg=qcol)

        # Live formula substitution
        self.fsub.config(
            text=(f"r = {self.I1.get():.2f}/{self.I2.get():.2f} = {r:.4f}\n"
                  f"= 2·√{r:.4f} / (1+{r:.4f})\n"
                  f"= {2*np.sqrt(r):.4f} / {1+r:.4f}\n"
                  f"= {V:.4f}")
        )

        # Main curve
        ax = self.ax_main
        ax.cla(); ax.set_facecolor(PANEL)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.fill_between(r_arr, V_arr, alpha=0.12, color=ACCENT)
        ax.plot(r_arr, V_arr, color=ACCENT, lw=2.4, label="V = 2√r/(1+r)")
        ax.axhspan(0.90, 1.00, alpha=0.07, color=ACCENT,  label="Excellent (V≥0.9)")
        ax.axhspan(0.70, 0.90, alpha=0.07, color=CYAN,    label="Good (0.7–0.9)")
        ax.axhspan(0.40, 0.70, alpha=0.07, color=ORANGE,  label="Moderate (0.4–0.7)")
        ax.axhspan(0.00, 0.40, alpha=0.07, color=MKRCLR,  label="Poor (<0.4)")
        ax.scatter([r], [V], s=180, color=MKRCLR, zorder=10,
                   edgecolors="white", linewidths=1.2)
        ax.axvline(r, color=MKRCLR, lw=1.2, ls=":")
        ax.axhline(V, color=MKRCLR, lw=1.2, ls=":")
        ax.text(r + self.zoom.get() * 0.01, V + 0.02,
                f"r={r:.2f}\nV={V:.3f}", color=MKRCLR, fontsize=8.5, va="bottom")
        ax.set_xlim(0, self.zoom.get()); ax.set_ylim(0, 1.05)
        ax.set_xlabel("Intensity Ratio  r = I₁ / I₂", fontsize=9)
        ax.set_ylabel("Visibility  V", fontsize=9)
        ax.set_title(f"Visibility vs Intensity Ratio  |  r={r:.3f}, V={V:.4f}",
                     color=TEXT, fontsize=10, pad=6)
        ax.legend(fontsize=7.5, facecolor=PANEL, edgecolor=HI,
                  labelcolor=TEXT, loc="upper right")
        for sp in ax.spines.values(): sp.set_edgecolor(HI)

        # Phasor
        ax2 = self.ax_phasor
        ax2.cla(); ax2.set_facecolor(PANEL); ax2.set_rlabel_position(60)
        E1 = np.sqrt(self.I1.get()); E2 = np.sqrt(self.I2.get())
        E_r   = np.sqrt(E1**2 + E2**2 + 2*E1*E2*np.cos(phi))
        phi_r = np.arctan2(E2*np.sin(phi), E1 + E2*np.cos(phi))
        ax2.plot([0, 0], [0, E1], color=CYAN,   lw=2.8, solid_capstyle="round")
        ax2.plot([0, phi], [0, E2], color=ORANGE, lw=2.8, solid_capstyle="round")
        ax2.plot([0, phi_r], [0, E_r], color=ACCENT, lw=2.8,
                 solid_capstyle="round", linestyle="--")
        ax2.scatter([0], [E1], s=60, color=CYAN, zorder=5)
        ax2.scatter([phi], [E2], s=60, color=ORANGE, zorder=5)
        ax2.scatter([phi_r], [E_r], s=60, color=ACCENT, zorder=5)
        r_max = max(E1, E2, E_r); off = r_max * 0.20
        ax2.text(0, E1+off, f"E₁={E1:.2f}", color=CYAN,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")
        lp = phi - 0.28 if abs(phi) < 0.3 else phi
        ax2.text(lp, E2+off, f"E₂={E2:.2f}", color=ORANGE,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax2.text(phi_r, E_r+off, f"|E|={E_r:.2f}", color=ACCENT,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")
        ax2.set_title("Phasor Diagram", color=TEXT, fontsize=9, pad=12)
        ax2.tick_params(colors=SUBTEXT, labelsize=7)
        ax2.spines["polar"].set_edgecolor(HI)

        # Heat-map
        ax3 = self.ax_heatmap
        ax3.cla(); ax3.set_facecolor(PANEL)
        N = 200
        i1v = np.linspace(0.01, 5, N); i2v = np.linspace(0.01, 5, N)
        I1g, I2g = np.meshgrid(i1v, i2v)
        Vg = 2*np.sqrt(I1g/I2g) / (1 + I1g/I2g)
        im = ax3.imshow(Vg, origin="lower", aspect="auto",
                        extent=[0.01, 5, 0.01, 5],
                        cmap="plasma", vmin=0, vmax=1, interpolation="bilinear")
        if self._cbar is not None:
            try: self._cbar.remove()
            except Exception: pass
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        div = make_axes_locatable(ax3)
        cax = div.append_axes("right", size="6%", pad=0.08)
        cax.set_facecolor(PANEL)
        self._cbar = self.fig.colorbar(im, cax=cax)
        self._cbar.set_label("Visibility V", color=TEXT, fontsize=8)
        self._cbar.ax.tick_params(colors=SUBTEXT, labelsize=7)
        self._cbar.ax.yaxis.label.set_color(TEXT)
        ax3.scatter([self.I1.get()], [self.I2.get()], s=130, color=MKRCLR,
                    zorder=10, edgecolors="white", linewidths=1.2)
        ax3.plot([0.01, 5], [0.01, 5], color="white", lw=1.2,
                 ls="--", alpha=0.5, label="I₁ = I₂  (V=1)")
        ax3.set_xlabel("I₁  (W)", fontsize=8)
        ax3.set_ylabel("I₂  (W)", fontsize=8)
        ax3.set_title("Visibility Map  (I₁ vs I₂)", fontsize=9, color=TEXT)
        ax3.legend(fontsize=7, facecolor=PANEL, edgecolor=HI,
                   labelcolor=TEXT, loc="lower right")
        for sp in ax3.spines.values(): sp.set_edgecolor(HI)

        self.canvas.draw_idle()

    def _apply_preset(self, vals):
        self.I1.set(vals["I1"]); self.I2.set(vals["I2"])
        self.phi.set(vals["phi"]); self.zoom.set(vals["zoom"])

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Export plot", defaultextension=".png",
            filetypes=[("PNG image", "*.png"),
                       ("PDF document", "*.pdf"),
                       ("SVG vector", "*.svg")])
        if path:
            self.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)

    def _reset(self):
        self.I1.set(1.0); self.I2.set(1.0)
        self.phi.set(0.0); self.zoom.set(10.0)


def main():
    root = tk.Tk()
    VisibilityRatioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()