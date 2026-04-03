"""
Simulation 2: Fringe Pattern
Full 2-D interference fringe pattern on a screen.
Sliders control: wavelength, slit separation, screen distance, I1, I2, and coherence.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LinearSegmentedColormap

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = "#0b0e18"
PANEL    = "#111520"
ACCENT   = "#7df9ff"
ACCENT2  = "#ff9f1c"
GOOD     = "#7fff7f"
TEXT     = "#dde4f0"
SUBTEXT  = "#666e88"
HI       = "#1e2538"
SLBG     = "#171d2e"

matplotlib.rcParams.update({
    "axes.facecolor":   PANEL,
    "figure.facecolor": BG,
    "axes.edgecolor":   HI,
    "axes.labelcolor":  TEXT,
    "xtick.color":      SUBTEXT,
    "ytick.color":      SUBTEXT,
    "text.color":       TEXT,
    "grid.color":       HI,
    "grid.linewidth":   0.5,
    "font.family":      "monospace",
})

# custom fringe colour map: dark-blue → white → dark-blue
_fringe_colors = [
    (0.04, 0.06, 0.14),
    (0.20, 0.40, 0.80),
    (1.00, 1.00, 1.00),
    (0.20, 0.40, 0.80),
    (0.04, 0.06, 0.14),
]
FRINGE_CMAP = LinearSegmentedColormap.from_list("fringe", _fringe_colors, N=512)


class FringePatternApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Fringe Pattern  ·  Fringe Visibility Analyzer")
        root.configure(bg=BG)
        root.geometry("1260x820")
        root.resizable(True, True)

        # Parameters
        self.lam   = tk.DoubleVar(value=550.0)   # wavelength nm
        self.d     = tk.DoubleVar(value=0.5)      # slit separation mm
        self.L     = tk.DoubleVar(value=1.0)      # screen distance m
        self.I1    = tk.DoubleVar(value=1.0)      # beam 1 intensity
        self.I2    = tk.DoubleVar(value=1.0)      # beam 2 intensity
        self.coh   = tk.DoubleVar(value=1.0)      # coherence factor 0→1
        self.theta = tk.DoubleVar(value=0.0)      # tilt angle degrees

        self._build_ui()
        self._update()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG, pady=8)
        hdr.pack(fill="x", padx=22)
        tk.Label(hdr, text="FRINGE PATTERN SIMULATOR",
                 font=("Courier", 20, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  Young's double-slit geometry",
                 font=("Courier", 11), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        ctrl = tk.Frame(main, bg=PANEL, width=310)
        ctrl.pack(side="left", fill="y", padx=(0, 12))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_canvas(right)

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(16, 3))
        tk.Label(f, text=text, font=("Courier", 8, "bold"),
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
                       orient="horizontal", length=265)
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
        tk.Label(parent, text="live fringe pattern updates",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        self._section(parent, "OPTICS")
        self._slider(parent, "Wavelength λ", self.lam,
                     380, 780, ACCENT, res=1, fmt="{:.0f}", unit=" nm")
        self._slider(parent, "Slit sep.  d", self.d,
                     0.05, 3.0, ACCENT2, res=0.01, fmt="{:.2f}", unit=" mm")
        self._slider(parent, "Screen dist L", self.L,
                     0.1, 3.0, GOOD, res=0.05, fmt="{:.2f}", unit=" m")

        self._section(parent, "BEAM INTENSITIES")
        self._slider(parent, "I₁  (Beam 1)", self.I1,
                     0.01, 2.0, "#7df9ff", res=0.01, fmt="{:.2f}", unit=" W")
        self._slider(parent, "I₂  (Beam 2)", self.I2,
                     0.01, 2.0, "#ff9f1c", res=0.01, fmt="{:.2f}", unit=" W")

        self._section(parent, "EXTRA EFFECTS")
        self._slider(parent, "Coherence γ", self.coh,
                     0.0, 1.0, "#d4aaff", res=0.01, fmt="{:.2f}", unit="")
        self._slider(parent, "Tilt angle θ", self.theta,
                     -30, 30, "#ff6b6b", res=0.5, fmt="{:.1f}", unit="°")

        self._section(parent, "LIVE METRICS")
        self.vis_var   = tk.StringVar(value="—")
        self.fringe_var= tk.StringVar(value="—")
        self.order_var = tk.StringVar(value="—")

        for lbl, var, col in [
            ("Visibility V",      self.vis_var,    GOOD),
            ("Fringe width β",    self.fringe_var, ACCENT),
            ("Bright orders ±N",  self.order_var,  ACCENT2),
        ]:
            row = tk.Frame(parent, bg=HI, pady=5, padx=10)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=lbl, font=("Courier", 9),
                     fg=SUBTEXT, bg=HI).pack(side="left")
            tk.Label(row, textvariable=var,
                     font=("Courier", 11, "bold"), fg=col,
                     bg=HI).pack(side="right")

        # Physics note
        note = tk.Frame(parent, bg="#07111f", pady=8, padx=10)
        note.pack(fill="x", padx=14, pady=(16, 0))
        tk.Label(note, text="YOUNG'S DSE",
                 font=("Courier", 8, "bold"), fg=ACCENT, bg="#07111f").pack()
        for txt in ["β = λL / d",
                    "V = γ · 2√(I₁I₂) / (I₁+I₂)",
                    "I(y) = (I₁+I₂)[1 + V·cos(2πdy/λL)]"]:
            tk.Label(note, text=txt, font=("Courier", 8),
                     fg=SUBTEXT, bg="#07111f").pack(pady=1)

        tk.Button(parent, text="⟳  RESET",
                  font=("Courier", 9, "bold"), fg=BG, bg=ACCENT,
                  relief="flat", bd=0, pady=5, cursor="hand2",
                  command=self._reset).pack(fill="x", padx=14, pady=14)

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(9.5, 7), facecolor=BG)
        gs = GridSpec(2, 2, figure=self.fig,
                      hspace=0.44, wspace=0.32,
                      left=0.08, right=0.97, top=0.93, bottom=0.08)
        self.ax2d  = self.fig.add_subplot(gs[0, :])  # 2-D fringe pattern
        self.ax1d  = self.fig.add_subplot(gs[1, 0])  # 1-D cross section
        self.ax_wl = self.fig.add_subplot(gs[1, 1])  # wavelength bar

        for ax in (self.ax2d, self.ax1d, self.ax_wl):
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_edgecolor(HI)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Physics ───────────────────────────────────────────────────────────────
    def _wavelength_to_rgb(self, wl_nm):
        """Very rough mapping of wavelength → RGB for display."""
        w = wl_nm
        if   380 <= w < 440: r,g,b = (440-w)/(440-380), 0, 1
        elif 440 <= w < 490: r,g,b = 0, (w-440)/(490-440), 1
        elif 490 <= w < 510: r,g,b = 0, 1, (510-w)/(510-490)
        elif 510 <= w < 580: r,g,b = (w-510)/(580-510), 1, 0
        elif 580 <= w < 645: r,g,b = 1, (645-w)/(645-580), 0
        elif 645 <= w <= 780: r,g,b = 1, 0, 0
        else:                 r,g,b = 0.5, 0.5, 0.5
        return (r, g, b)

    def _compute(self):
        lam   = self.lam.get() * 1e-9
        d     = self.d.get()   * 1e-3
        L     = self.L.get()
        I1    = self.I1.get()
        I2    = self.I2.get()
        coh   = self.coh.get()
        theta = np.deg2rad(self.theta.get())

        beta  = lam * L / d                  # fringe width (m)
        I_max = (np.sqrt(I1) + np.sqrt(I2))**2
        I_min = (np.sqrt(I1) - np.sqrt(I2))**2
        V_max = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) > 0 else 0
        V     = coh * V_max

        # 1-D cross section (y axis on screen)
        y = np.linspace(-5 * beta, 5 * beta, 2000)
        delta = (2 * np.pi * d / (lam * L)) * (y + L * np.tan(theta))
        I1D   = (I1 + I2) * (1 + V * np.cos(delta))

        # 2-D pattern
        y2d = np.linspace(-5 * beta, 5 * beta, 400)
        x2d = np.linspace(-2 * beta, 2 * beta, 200)
        Y, X = np.meshgrid(y2d, x2d, indexing="ij")
        delta2d = (2 * np.pi * d / (lam * L)) * (Y + L * np.tan(theta))
        I2D = (I1 + I2) * (1 + V * np.cos(delta2d))

        # Gaussian envelope (finite slit width)
        sigma = 8 * beta
        env   = np.exp(-Y**2 / (2 * sigma**2))
        I2D   = I2D * env

        n_orders = int(5)
        return y, I1D, y2d, x2d, I2D, beta, V, n_orders

    # ── Render ────────────────────────────────────────────────────────────────
    def _update(self, *_):
        y, I1D, y2d, x2d, I2D, beta, V, n_orders = self._compute()

        lam_nm = self.lam.get()
        rgb    = self._wavelength_to_rgb(lam_nm)
        beta_mm = beta * 1e3

        self.vis_var.set(f"{V:.4f}")
        self.fringe_var.set(f"{beta_mm:.3f} mm")
        self.order_var.set(f"± {n_orders}")

        # ── 2-D fringe image ─────────────────────────────────────────────────
        ax = self.ax2d
        ax.cla()
        ax.set_facecolor("#000")
        ext = [y2d[0]*1e3, y2d[-1]*1e3, x2d[0]*1e3, x2d[-1]*1e3]
        ax.imshow(I2D.T, aspect="auto", extent=ext, origin="lower",
                  cmap=FRINGE_CMAP, interpolation="bilinear")
        ax.set_xlabel("Screen position y (mm)", fontsize=9)
        ax.set_ylabel("x (mm)", fontsize=9)
        ax.set_title(
            f"2-D Fringe Pattern  |  λ={lam_nm:.0f} nm  "
            f"d={self.d.get():.2f} mm  L={self.L.get():.2f} m  "
            f"V={V:.3f}",
            color=TEXT, fontsize=10, pad=6)
        for sp in ax.spines.values():
            sp.set_edgecolor(HI)

        # ── 1-D cross-section ────────────────────────────────────────────────
        ax1 = self.ax1d
        ax1.cla()
        ax1.set_facecolor(PANEL)
        ax1.grid(True, linestyle="--", alpha=0.35)
        ax1.fill_between(y*1e3, I1D, alpha=0.2, color=rgb)
        ax1.plot(y*1e3, I1D, color=rgb, lw=1.8)
        ax1.set_xlabel("Screen position y (mm)", fontsize=8)
        ax1.set_ylabel("Intensity (a.u.)", fontsize=8)
        ax1.set_title("1-D Intensity Cross-section", fontsize=9, color=TEXT)
        # Mark fringe width
        ax1.annotate("", xy=(beta_mm/2, I1D.max()*0.92),
                     xytext=(-beta_mm/2, I1D.max()*0.92),
                     arrowprops=dict(arrowstyle="<->", color=ACCENT2, lw=1.5))
        ax1.text(0, I1D.max()*0.96, f"β={beta_mm:.2f} mm",
                 color=ACCENT2, ha="center", fontsize=8)
        for sp in ax1.spines.values():
            sp.set_edgecolor(HI)

        # ── Wavelength colour bar ─────────────────────────────────────────────
        ax2 = self.ax_wl
        ax2.cla()
        ax2.set_facecolor(PANEL)
        wl_arr = np.linspace(380, 780, 500)
        colors_wl = [self._wavelength_to_rgb(w) for w in wl_arr]
        cmap_wl   = LinearSegmentedColormap.from_list("visible", colors_wl, N=500)
        grad = np.linspace(0, 1, 256).reshape(1, -1)
        ax2.imshow(grad, aspect="auto", extent=[380, 780, 0, 1],
                   cmap=cmap_wl, origin="lower")
        ax2.axvline(lam_nm, color="white", lw=2.2, ls="--")
        ax2.text(lam_nm, 1.06, f"{lam_nm:.0f} nm",
                 color="white", ha="center", fontsize=9, transform=ax2.get_xaxis_transform())
        ax2.set_xlabel("Wavelength (nm)", fontsize=8)
        ax2.set_yticks([])
        ax2.set_title("Visible Spectrum", fontsize=9, color=TEXT)
        for sp in ax2.spines.values():
            sp.set_edgecolor(HI)

        self.canvas.draw_idle()

    def _reset(self):
        self.lam.set(550)
        self.d.set(0.5)
        self.L.set(1.0)
        self.I1.set(1.0)
        self.I2.set(1.0)
        self.coh.set(1.0)
        self.theta.set(0.0)


def main():
    root = tk.Tk()
    app = FringePatternApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
