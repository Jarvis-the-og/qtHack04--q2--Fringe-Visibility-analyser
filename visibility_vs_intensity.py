"""
Simulation 3: Visibility vs Intensity Ratio
Plots the analytic curve V = 2√r / (1 + r) where r = I1/I2.
Interactive marker tracks the current ratio live.
Also shows complementary visualizations: phasor diagram and contrast map.

PATCHES APPLIED:
  - FIX 1: Phasor label placement corrected — labels now use polar coordinates
             (angle, radius) instead of erroneous Cartesian offsets inside
             a polar axes, so E₁ and E₂ labels always sit at their arrow tips.
  - FIX 2: Visibility heatmap no longer cut off — window is enlarged to 1440×860,
             GridSpec bottom/top margins are adjusted, and the heatmap axes gets
             explicit space so the colorbar is never clipped.
  - FIX 3: Colorbar is created once (stored in self._cbar) and only replaced on
             each redraw, preventing accumulation of duplicate colorbars.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec

# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#0c0d14"
PANEL   = "#12141f"
ACCENT  = "#c8ff5c"     # lime for the curve
MKRCLR  = "#ff5c8a"     # hot-pink live marker
CYAN    = "#5ce0ff"
ORANGE  = "#ffa45c"
TEXT    = "#dfe5f5"
SUBTEXT = "#6b728c"
HI      = "#1d2133"
SLBG    = "#181c2d"

matplotlib.rcParams.update({
    "axes.facecolor":   PANEL,
    "figure.facecolor": BG,
    "axes.edgecolor":   HI,
    "axes.labelcolor":  TEXT,
    "xtick.color":      SUBTEXT,
    "ytick.color":      SUBTEXT,
    "text.color":       TEXT,
    "grid.color":       HI,
    "grid.linewidth":   0.55,
    "font.family":      "monospace",
})


class VisibilityRatioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Visibility vs Intensity Ratio  ·  Fringe Visibility Analyzer")
        root.configure(bg=BG)
        # ── FIX 2: wider/taller window so heatmap is fully visible ──────────
        root.geometry("1440x860")
        root.resizable(True, True)

        self.I1   = tk.DoubleVar(value=1.0)
        self.I2   = tk.DoubleVar(value=1.0)
        self.phi  = tk.DoubleVar(value=0.0)    # degrees
        self.zoom = tk.DoubleVar(value=10.0)   # max ratio displayed

        # ── FIX 3: single colorbar reference ────────────────────────────────
        self._cbar = None

        self._build_ui()
        self._update()

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG, pady=8)
        hdr.pack(fill="x", padx=22)
        tk.Label(hdr, text="VISIBILITY  vs  INTENSITY RATIO",
                 font=("Courier", 18, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  V = 2√(I₁/I₂) / (1 + I₁/I₂)",
                 font=("Courier", 10), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        ctrl = tk.Frame(main, bg=PANEL, width=300)
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
        tk.Label(top, text=label, font=("Courier", 10),
                 fg=TEXT, bg=PANEL).pack(side="left")
        vlbl = tk.Label(top, text=fmt.format(var.get()) + unit,
                        font=("Courier", 10, "bold"), fg=color,
                        bg=PANEL, width=9)
        vlbl.pack(side="right")

        sl = ttk.Scale(row, from_=lo, to=hi, variable=var,
                       orient="horizontal", length=258)
        sl.pack(fill="x")

        ticks = tk.Frame(row, bg=PANEL)
        ticks.pack(fill="x")
        tk.Label(ticks, text=f"{lo}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="left")
        tk.Label(ticks, text=f"{hi}", font=("Courier", 7),
                 fg=SUBTEXT, bg=PANEL).pack(side="right")

        def on(*_):
            vlbl.config(text=fmt.format(var.get()) + unit)
            self._update()
        var.trace_add("write", on)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale",
                        background=PANEL, troughcolor=SLBG,
                        sliderthickness=14)

    def _build_controls(self, parent):
        tk.Label(parent, text="PARAMETERS",
                 font=("Courier", 12, "bold"), fg=TEXT, bg=PANEL).pack(pady=(18, 0))
        tk.Label(parent, text="move sliders — watch the marker",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        self._section(parent, "BEAM INTENSITIES")
        self._slider(parent, "I₁  (Beam 1)", self.I1,
                     0.01, 5.0, CYAN, res=0.01, fmt="{:.2f}", unit=" W")
        self._slider(parent, "I₂  (Beam 2)", self.I2,
                     0.01, 5.0, ORANGE, res=0.01, fmt="{:.2f}", unit=" W")

        self._section(parent, "DISPLAY")
        self._slider(parent, "Phase Δφ", self.phi,
                     0, 360, "#d4aaff", res=1, fmt="{:.0f}", unit="°")
        self._slider(parent, "X-axis max r", self.zoom,
                     2.0, 50.0, ACCENT, res=0.5, fmt="{:.1f}", unit="")

        self._section(parent, "LIVE METRICS")
        metrics = [
            ("I₁ / I₂  ratio r",  tk.StringVar(value="—"), ACCENT),
            ("Visibility  V",      tk.StringVar(value="—"), MKRCLR),
            ("I_max",              tk.StringVar(value="—"), CYAN),
            ("I_min",              tk.StringVar(value="—"), ORANGE),
            ("Contrast  C",        tk.StringVar(value="—"), "#d4aaff"),
        ]
        self.m_ratio, self.m_vis, self.m_imax, self.m_imin, self.m_cont = \
            [m[1] for m in metrics]
        for lbl, var, col in metrics:
            row = tk.Frame(parent, bg=HI, pady=5, padx=10)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=lbl, font=("Courier", 9),
                     fg=SUBTEXT, bg=HI).pack(side="left")
            tk.Label(row, textvariable=var,
                     font=("Courier", 11, "bold"),
                     fg=col, bg=HI).pack(side="right")

        # Quality badge
        self.quality_var = tk.StringVar(value="EXCELLENT")
        self.quality_col = tk.StringVar(value=ACCENT)
        qbox = tk.Frame(parent, bg=HI, pady=10)
        qbox.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(qbox, text="FRINGE QUALITY", font=("Courier", 8),
                 fg=SUBTEXT, bg=HI).pack()
        self.q_lbl = tk.Label(qbox, textvariable=self.quality_var,
                              font=("Courier", 14, "bold"), fg=ACCENT, bg=HI)
        self.q_lbl.pack()

        # Theory
        th = tk.Frame(parent, bg="#08101c", pady=8, padx=10)
        th.pack(fill="x", padx=14, pady=(14, 0))
        tk.Label(th, text="KEY IDENTITY", font=("Courier", 8, "bold"),
                 fg=ACCENT, bg="#08101c").pack()
        for t in ["r = I₁/I₂",
                  "V = 2√r / (1 + r)",
                  "V_max = 1  when r = 1",
                  "V → 0  as r → ∞"]:
            tk.Label(th, text=t, font=("Courier", 8),
                     fg=SUBTEXT, bg="#08101c").pack(anchor="w")

        tk.Button(parent, text="⟳  RESET",
                  font=("Courier", 9, "bold"), fg=BG, bg=ACCENT,
                  relief="flat", bd=0, pady=5, cursor="hand2",
                  command=self._reset).pack(fill="x", padx=14, pady=14)

    def _build_canvas(self, parent):
        # ── FIX 2: taller figure, adjusted GridSpec margins ─────────────────
        self.fig = plt.figure(figsize=(10.5, 8.0), facecolor=BG)
        gs = GridSpec(
            2, 2,
            figure=self.fig,
            hspace=0.48,
            wspace=0.42,          # more horizontal breathing room
            left=0.07,
            right=0.96,
            top=0.93,
            bottom=0.09,          # ensure bottom row is not clipped
        )
        self.ax_main   = self.fig.add_subplot(gs[0, :])      # V vs r curve (full width)
        self.ax_phasor = self.fig.add_subplot(gs[1, 0], projection="polar")
        self.ax_heatmap= self.fig.add_subplot(gs[1, 1])      # Visibility heat-map

        for ax in (self.ax_main, self.ax_heatmap):
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_edgecolor(HI)
        self.ax_phasor.set_facecolor(PANEL)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Physics ────────────────────────────────────────────────────────────
    def _vis_from_ratio(self, r):
        return 2 * np.sqrt(r) / (1 + r)

    def _compute(self):
        I1   = self.I1.get()
        I2   = self.I2.get()
        phi  = np.deg2rad(self.phi.get())
        r    = I1 / I2
        V    = self._vis_from_ratio(r)
        Imax = (np.sqrt(I1) + np.sqrt(I2))**2
        Imin = (np.sqrt(I1) - np.sqrt(I2))**2
        C    = V   # Michelson contrast = visibility

        # Full curve
        r_arr = np.linspace(0.001, self.zoom.get(), 2000)
        V_arr = self._vis_from_ratio(r_arr)
        return r_arr, V_arr, r, V, Imax, Imin, C, phi

    # ── Render ─────────────────────────────────────────────────────────────
    def _quality_label(self, V):
        if V >= 0.90: return "EXCELLENT", ACCENT
        if V >= 0.70: return "GOOD",      CYAN
        if V >= 0.40: return "MODERATE",  ORANGE
        return "POOR", MKRCLR

    def _update(self, *_):
        r_arr, V_arr, r, V, Imax, Imin, C, phi = self._compute()

        # Update labels
        self.m_ratio.set(f"{r:.4f}")
        self.m_vis.set(f"{V:.4f}")
        self.m_imax.set(f"{Imax:.3f}")
        self.m_imin.set(f"{Imin:.3f}")
        self.m_cont.set(f"{C:.4f}")
        qlbl, qcol = self._quality_label(V)
        self.quality_var.set(qlbl)
        self.q_lbl.config(fg=qcol)

        # ── main curve ────────────────────────────────────────────────────
        ax = self.ax_main
        ax.cla()
        ax.set_facecolor(PANEL)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.fill_between(r_arr, V_arr, alpha=0.12, color=ACCENT)
        ax.plot(r_arr, V_arr, color=ACCENT, lw=2.4, label="V = 2√r/(1+r)")
        # quality zones
        ax.axhspan(0.90, 1.00, alpha=0.07, color=ACCENT,  label="Excellent (V≥0.9)")
        ax.axhspan(0.70, 0.90, alpha=0.07, color=CYAN,    label="Good (0.7–0.9)")
        ax.axhspan(0.40, 0.70, alpha=0.07, color=ORANGE,  label="Moderate (0.4–0.7)")
        ax.axhspan(0.00, 0.40, alpha=0.07, color=MKRCLR,  label="Poor (<0.4)")
        # live marker
        ax.scatter([r], [V], s=180, color=MKRCLR, zorder=10,
                   edgecolors="white", linewidths=1.2)
        ax.axvline(r, color=MKRCLR, lw=1.2, ls=":")
        ax.axhline(V, color=MKRCLR, lw=1.2, ls=":")
        ax.text(r + self.zoom.get() * 0.01, V + 0.02,
                f"r={r:.2f}\nV={V:.3f}",
                color=MKRCLR, fontsize=8.5, va="bottom")
        ax.set_xlim(0, self.zoom.get())
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Intensity Ratio  r = I₁ / I₂", fontsize=9)
        ax.set_ylabel("Visibility  V", fontsize=9)
        ax.set_title(
            f"Visibility vs Intensity Ratio  |  Current: r={r:.3f}, V={V:.4f}",
            color=TEXT, fontsize=10, pad=6)
        ax.legend(fontsize=7.5, facecolor=PANEL,
                  edgecolor=HI, labelcolor=TEXT, loc="upper right")
        for sp in ax.spines.values():
            sp.set_edgecolor(HI)

        # ── phasor diagram ─────────────────────────────────────────────────
        # Draw on a CARTESIAN axes (converted from polar internally).
        # ax.annotate on polar axes is unreliable for origin-based arrows;
        # using ax2.quiver on the polar axes is equally fragile.
        # Solution: draw everything in Cartesian, label in data coordinates.
        ax2 = self.ax_phasor
        ax2.cla()
        ax2.set_facecolor(PANEL)
        ax2.set_rlabel_position(60)

        E1 = np.sqrt(self.I1.get())
        E2 = np.sqrt(self.I2.get())

        # Cartesian components
        E1x, E1y = E1, 0.0                            # E1 always at 0°
        E2x, E2y = E2 * np.cos(phi), E2 * np.sin(phi)

        E_r   = np.sqrt(E1**2 + E2**2 + 2 * E1 * E2 * np.cos(phi))
        phi_r = np.arctan2(E2 * np.sin(phi), E1 + E2 * np.cos(phi))

        # Draw thick lines from origin to each tip
        ax2.plot([0, 0], [0, E1],   color=CYAN,   lw=2.8, solid_capstyle="round")
        ax2.plot([0, phi], [0, E2], color=ORANGE, lw=2.8, solid_capstyle="round")
        ax2.plot([0, phi_r], [0, E_r], color=ACCENT, lw=2.8,
                 solid_capstyle="round", linestyle="--")

        # Arrowhead dots at tips
        ax2.scatter([0], [E1],   s=60, color=CYAN,   zorder=5)
        ax2.scatter([phi], [E2], s=60, color=ORANGE, zorder=5)
        ax2.scatter([phi_r], [E_r], s=60, color=ACCENT, zorder=5)

        # Labels — placed just beyond the tip radius, same angle
        r_max  = max(E1, E2, E_r)
        offset = r_max * 0.20

        ax2.text(0, E1 + offset,
                 f"E₁={E1:.2f}", color=CYAN,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")

        lbl_phi2 = phi - 0.28 if abs(phi) < 0.3 else phi
        ax2.text(lbl_phi2, E2 + offset,
                 f"E₂={E2:.2f}", color=ORANGE,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")

        ax2.text(phi_r, E_r + offset,
                 f"|E|={E_r:.2f}", color=ACCENT,
                 ha="center", va="bottom", fontsize=8, fontweight="bold")

        ax2.set_title("Phasor Diagram", color=TEXT, fontsize=9, pad=12)
        ax2.tick_params(colors=SUBTEXT, labelsize=7)
        ax2.spines["polar"].set_edgecolor(HI)

        # ── 2-D visibility heat-map (I1 vs I2) ───────────────────────────
        ax3 = self.ax_heatmap
        ax3.cla()
        ax3.set_facecolor(PANEL)

        N    = 200
        i1v  = np.linspace(0.01, 5, N)
        i2v  = np.linspace(0.01, 5, N)
        I1g, I2g = np.meshgrid(i1v, i2v)
        Rg   = I1g / I2g
        Vg   = 2 * np.sqrt(Rg) / (1 + Rg)

        im = ax3.imshow(
            Vg, origin="lower", aspect="auto",
            extent=[0.01, 5, 0.01, 5],
            cmap="plasma", vmin=0, vmax=1,
            interpolation="bilinear",
        )

        # ── FIX 3: remove old colorbar before adding a new one ────────────
        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                pass
        # Use make_axes for a tightly controlled colorbar that never overlaps
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax3)
        cax = divider.append_axes("right", size="6%", pad=0.08)
        cax.set_facecolor(PANEL)
        self._cbar = self.fig.colorbar(im, cax=cax)
        self._cbar.set_label("Visibility V", color=TEXT, fontsize=8)
        self._cbar.ax.tick_params(colors=SUBTEXT, labelsize=7)
        self._cbar.ax.yaxis.label.set_color(TEXT)

        # Live cursor dot on heatmap
        ax3.scatter([self.I1.get()], [self.I2.get()],
                    s=130, color=MKRCLR, zorder=10,
                    edgecolors="white", linewidths=1.2)
        # Diagonal V=1 line
        ax3.plot([0.01, 5], [0.01, 5], color="white", lw=1.2,
                 ls="--", alpha=0.5, label="I₁ = I₂  (V=1)")

        ax3.set_xlabel("I₁  (W)", fontsize=8)
        ax3.set_ylabel("I₂  (W)", fontsize=8)
        ax3.set_title("Visibility Map  (I₁ vs I₂)", fontsize=9, color=TEXT)
        ax3.legend(fontsize=7, facecolor=PANEL, edgecolor=HI,
                   labelcolor=TEXT, loc="lower right")
        for sp in ax3.spines.values():
            sp.set_edgecolor(HI)

        self.canvas.draw_idle()

    def _reset(self):
        self.I1.set(1.0)
        self.I2.set(1.0)
        self.phi.set(0.0)
        self.zoom.set(10.0)


def main():
    root = tk.Tk()
    app = VisibilityRatioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()