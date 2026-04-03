"""
Simulation 1: Two Beams Variation
Demonstrates how unequal beam intensities affect the combined intensity profile
and fringe visibility in real time.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
import matplotlib.patches as mpatches

# ── Colour Palette ──────────────────────────────────────────────────────────
BG        = "#0d0f14"
PANEL     = "#13161e"
ACCENT1   = "#00d4ff"   # beam 1  (cyan)
ACCENT2   = "#ff6b35"   # beam 2  (orange)
COMBINED  = "#b8ff6b"   # resultant (lime)
TEXT      = "#e8ecf4"
SUBTEXT   = "#7a8099"
SLIDER_BG = "#1c2030"
HIGHLIGHT = "#252a3a"

matplotlib.rcParams.update({
    "axes.facecolor":  PANEL,
    "figure.facecolor": BG,
    "axes.edgecolor":  HIGHLIGHT,
    "axes.labelcolor": TEXT,
    "xtick.color":     SUBTEXT,
    "ytick.color":     SUBTEXT,
    "text.color":      TEXT,
    "grid.color":      HIGHLIGHT,
    "grid.linewidth":  0.6,
    "font.family":     "monospace",
})


class TwoBeamsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Two Beams Variation  ·  Fringe Visibility Analyzer")
        root.configure(bg=BG)
        root.geometry("1200x780")
        root.resizable(True, True)

        # ── State variables ─────────────────────────────────────────────────
        self.I1  = tk.DoubleVar(value=1.0)
        self.I2  = tk.DoubleVar(value=1.0)
        self.phi = tk.DoubleVar(value=0.0)   # phase offset in degrees
        self.k   = tk.DoubleVar(value=4.0)   # spatial frequency

        self._build_ui()
        self._update()

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG, pady=10)
        hdr.pack(fill="x", padx=20)
        tk.Label(hdr, text="TWO BEAMS VARIATION",
                 font=("Courier", 20, "bold"), fg=ACCENT1, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  interference intensity & fringe quality",
                 font=("Courier", 11), fg=SUBTEXT, bg=BG).pack(side="left", pady=6)

        # Main layout
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Left: control panel
        ctrl = tk.Frame(main, bg=PANEL, relief="flat", bd=0, width=300)
        ctrl.pack(side="left", fill="y", padx=(0, 12), pady=0)
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        # Right: matplotlib canvas
        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side="left", fill="both", expand=True)
        self._build_canvas(canvas_frame)

    def _section_label(self, parent, text):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(18, 4))
        tk.Label(f, text=text, font=("Courier", 9, "bold"),
                 fg=ACCENT1, bg=PANEL).pack(side="left")
        tk.Frame(f, bg=HIGHLIGHT, height=1).pack(side="left", fill="x",
                                                  expand=True, padx=(8, 0))

    def _add_slider(self, parent, label, var, from_, to, color,
                    resolution=0.01, fmt="{:.2f}", unit=""):
        row = tk.Frame(parent, bg=PANEL, pady=4)
        row.pack(fill="x", padx=14)
        top = tk.Frame(row, bg=PANEL)
        top.pack(fill="x")
        tk.Label(top, text=label, font=("Courier", 10), fg=TEXT,
                 bg=PANEL).pack(side="left")
        val_lbl = tk.Label(top, text=fmt.format(var.get()) + unit,
                           font=("Courier", 10, "bold"), fg=color, bg=PANEL, width=8)
        val_lbl.pack(side="right")

        sl = ttk.Scale(row, from_=from_, to=to, variable=var,
                       orient="horizontal", length=250)
        sl.pack(fill="x")

        def on_change(*_):
            val_lbl.config(text=fmt.format(var.get()) + unit)
            self._update()

        var.trace_add("write", on_change)

        # Tick marks (min / max)
        ticks = tk.Frame(row, bg=PANEL)
        ticks.pack(fill="x")
        tk.Label(ticks, text=f"{from_}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="left")
        tk.Label(ticks, text=f"{to}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale",
                        background=PANEL, troughcolor=SLIDER_BG,
                        sliderthickness=14)
        return val_lbl

    def _build_controls(self, parent):
        tk.Label(parent, text="PARAMETERS", font=("Courier", 12, "bold"),
                 fg=TEXT, bg=PANEL).pack(pady=(20, 0))
        tk.Label(parent, text="adjust sliders to see live changes",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        self._section_label(parent, "BEAM INTENSITIES")
        self._add_slider(parent, "I₁  (Beam 1)", self.I1, 0.01, 2.0,
                         ACCENT1, fmt="{:.2f}", unit=" W")
        self._add_slider(parent, "I₂  (Beam 2)", self.I2, 0.01, 2.0,
                         ACCENT2, fmt="{:.2f}", unit=" W")

        self._section_label(parent, "WAVE PROPERTIES")
        self._add_slider(parent, "Phase Δφ", self.phi, 0, 360,
                         COMBINED, resolution=1, fmt="{:.0f}", unit="°")
        self._add_slider(parent, "Freq  k", self.k, 1.0, 12.0,
                         "#d4aaff", resolution=0.1, fmt="{:.1f}", unit="")

        self._section_label(parent, "LIVE METRICS")
        self.vis_var  = tk.StringVar(value="—")
        self.imax_var = tk.StringVar(value="—")
        self.imin_var = tk.StringVar(value="—")
        self.ratio_var= tk.StringVar(value="—")

        metrics = [
            ("Visibility  V", self.vis_var,  COMBINED),
            ("I_max",         self.imax_var, ACCENT1),
            ("I_min",         self.imin_var, ACCENT2),
            ("I₁ / I₂",       self.ratio_var,"#d4aaff"),
        ]
        for lbl, var, col in metrics:
            row = tk.Frame(parent, bg=HIGHLIGHT, pady=6, padx=10)
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=lbl, font=("Courier", 9), fg=SUBTEXT,
                     bg=HIGHLIGHT).pack(side="left")
            tk.Label(row, textvariable=var, font=("Courier", 11, "bold"),
                     fg=col, bg=HIGHLIGHT).pack(side="right")

        # Formula box
        fbox = tk.Frame(parent, bg="#0a1a2a", pady=10, padx=12)
        fbox.pack(fill="x", padx=14, pady=(20, 0))
        tk.Label(fbox, text="VISIBILITY FORMULA",
                 font=("Courier", 8, "bold"), fg=ACCENT1, bg="#0a1a2a").pack()
        tk.Label(fbox, text="V = 2√(I₁·I₂) / (I₁ + I₂)",
                 font=("Courier", 10), fg=TEXT, bg="#0a1a2a").pack(pady=4)
        tk.Label(fbox, text="I(x) = I₁ + I₂ + 2√(I₁·I₂)·cos(kx+Δφ)",
                 font=("Courier", 8), fg=SUBTEXT, bg="#0a1a2a",
                 wraplength=260, justify="center").pack()

        # Reset
        tk.Button(parent, text="⟳  RESET DEFAULTS",
                  font=("Courier", 9, "bold"), fg=BG, bg=ACCENT1,
                  relief="flat", bd=0, pady=6, cursor="hand2",
                  command=self._reset).pack(fill="x", padx=14, pady=20)

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(9, 6.5), facecolor=BG, tight_layout=False)
        self.fig.subplots_adjust(hspace=0.42, left=0.09, right=0.97,
                                 top=0.93, bottom=0.08)
        gs = GridSpec(2, 2, figure=self.fig)
        self.ax_main  = self.fig.add_subplot(gs[0, :])   # top: combined pattern
        self.ax_beam1 = self.fig.add_subplot(gs[1, 0])   # bottom-left: beam 1
        self.ax_beam2 = self.fig.add_subplot(gs[1, 1])   # bottom-right: beam 2

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

        I_combined = (I1 + I2
                      + 2 * np.sqrt(I1 * I2) * np.cos(k * x + phi))
        I_beam1    = I1 * (1 + np.cos(k * x))
        I_beam2    = I2 * (1 + np.cos(k * x + phi + np.pi / 4))

        I_max = (np.sqrt(I1) + np.sqrt(I2)) ** 2
        I_min = (np.sqrt(I1) - np.sqrt(I2)) ** 2
        V     = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) > 0 else 0

        return x, I_beam1, I_beam2, I_combined, I_max, I_min, V

    # ── Rendering ────────────────────────────────────────────────────────────
    def _update(self, *_):
        x, ib1, ib2, icom, imax, imin, V = self._compute()
        I1, I2 = self.I1.get(), self.I2.get()

        # ── metrics labels ───────────────────────────────────────────────────
        self.vis_var.set(f"{V:.4f}")
        self.imax_var.set(f"{imax:.3f}")
        self.imin_var.set(f"{imin:.3f}")
        self.ratio_var.set(f"{I1 / I2:.3f}")

        # ── top plot: combined ───────────────────────────────────────────────
        ax = self.ax_main
        ax.cla()
        ax.set_facecolor(PANEL)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.fill_between(x, icom, alpha=0.18, color=COMBINED)
        ax.plot(x, icom, color=COMBINED, lw=2.2, label="Combined I(x)")
        ax.axhline(imax, color=ACCENT1, lw=1.1, ls="--",
                   label=f"I_max = {imax:.3f}")
        ax.axhline(imin, color=ACCENT2, lw=1.1, ls="--",
                   label=f"I_min = {imin:.3f}")
        ax.set_title(f"Combined Intensity Pattern   |   Visibility V = {V:.4f}",
                     color=TEXT, fontsize=11, pad=8)
        ax.set_xlabel("Position  x  (rad)", fontsize=9)
        ax.set_ylabel("Intensity (a.u.)", fontsize=9)
        ax.legend(loc="upper right", fontsize=8,
                  facecolor=PANEL, edgecolor=HIGHLIGHT, labelcolor=TEXT)
        # Colour gradient fringe overlay
        extent = [x[0], x[-1], 0, icom.max() * 1.05]
        ax.imshow(np.tile(np.cos(self.k.get() * x + np.deg2rad(self.phi.get())),
                          (30, 1)),
                  aspect="auto", extent=extent, alpha=0.06,
                  cmap="bwr", origin="lower")
        ax.set_ylim(0, icom.max() * 1.12)
        for sp in ax.spines.values():
            sp.set_edgecolor(HIGHLIGHT)

        # ── bottom-left: beam 1 ──────────────────────────────────────────────
        ax1 = self.ax_beam1
        ax1.cla()
        ax1.set_facecolor(PANEL)
        ax1.grid(True, linestyle="--", alpha=0.35)
        ax1.fill_between(x, ib1, alpha=0.15, color=ACCENT1)
        ax1.plot(x, ib1, color=ACCENT1, lw=1.8)
        ax1.set_title(f"Beam 1   I₁ = {I1:.2f} W", color=ACCENT1, fontsize=9)
        ax1.set_xlabel("Position  x", fontsize=8)
        ax1.set_ylabel("Intensity", fontsize=8)
        for sp in ax1.spines.values():
            sp.set_edgecolor(HIGHLIGHT)

        # ── bottom-right: beam 2 ─────────────────────────────────────────────
        ax2 = self.ax_beam2
        ax2.cla()
        ax2.set_facecolor(PANEL)
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

    def _reset(self):
        self.I1.set(1.0)
        self.I2.set(1.0)
        self.phi.set(0.0)
        self.k.set(4.0)


def main():
    root = tk.Tk()
    app = TwoBeamsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
