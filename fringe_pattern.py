"""
Fringe Pattern Simulator — Enhanced Edition
============================================
Enhancements over base version:
  • Path difference Δx slider  →  φ = 2πΔx/λ  shifts fringes
  • Full interference model: I = I₁+I₂+2√(I₁I₂)·γ·cos(k·y + φ)
  • Live physics readout: Δx, φ (rad), formula substitution
  • Animation toggle — Δx sweeps automatically (moving fringes)
  • Central-maximum marker tracks shift
  • Tilt angle θ still works independently
  • All original features preserved
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

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0b0e18"
PANEL   = "#111520"
ACCENT  = "#7df9ff"
ACCENT2 = "#ff9f1c"
GOOD    = "#7fff7f"
PURPLE  = "#d4aaff"
RED     = "#ff6b6b"
TEXT    = "#dde4f0"
SUBTEXT = "#666e88"
HI      = "#1e2538"
SLBG    = "#171d2e"
GOLD    = "#ffd700"

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

_fringe_colors = [
    (0.04, 0.06, 0.14),
    (0.20, 0.40, 0.80),
    (1.00, 1.00, 1.00),
    (0.20, 0.40, 0.80),
    (0.04, 0.06, 0.14),
]
FRINGE_CMAP = LinearSegmentedColormap.from_list("fringe", _fringe_colors, N=512)


class FringePatternApp:
    # ── animation state ───────────────────────────────────────────────────────
    _anim_id    = None
    _anim_phase = 0.0          # internal phase accumulator for animation (μm)
    _anim_dir   = 1

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Fringe Pattern Simulator  ·  Enhanced Edition")
        root.configure(bg=BG)
        root.geometry("1380x880")
        root.resizable(True, True)

        # ── Physics parameters ─────────────────────────────────────────────
        self.lam    = tk.DoubleVar(value=550.0)   # nm
        self.d      = tk.DoubleVar(value=0.5)     # mm
        self.L      = tk.DoubleVar(value=1.0)     # m
        self.I1     = tk.DoubleVar(value=1.0)
        self.I2     = tk.DoubleVar(value=1.0)
        self.coh    = tk.DoubleVar(value=1.0)
        self.theta  = tk.DoubleVar(value=0.0)     # degrees
        self.delta_x = tk.DoubleVar(value=0.0)   # μm  ← NEW

        self._build_ui()
        self._update()

    # ─────────────────────────────────────────────────────────────────────────
    # UI helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _section(self, parent, text):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(16, 3))
        tk.Label(f, text=text, font=("Courier", 8, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Frame(f, bg=HI, height=1).pack(
            side="left", fill="x", expand=True, padx=(6, 0))

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
                        bg=PANEL, width=11)
        vlbl.pack(side="right")

        sl = ttk.Scale(row, from_=lo, to=hi, variable=var,
                       orient="horizontal", length=275)
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
        return sl

    # ── Full UI layout ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header row with Reset top-right ──────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG, pady=8)
        hdr.pack(fill="x", padx=22)
        tk.Label(hdr, text="FRINGE PATTERN SIMULATOR",
                 font=("Courier", 20, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr,
                 text="  ·  Young's DSE  |  Path Difference  |  Phase Control",
                 font=("Courier", 11), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)
        # Reset button fixed top-right in header
        tk.Button(hdr, text="⟳  RESET",
                  font=("Courier", 10, "bold"), fg=BG, bg=ACCENT,
                  relief="flat", bd=0, padx=16, pady=6, cursor="hand2",
                  command=self._reset).pack(side="right", padx=(0, 4))

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        ctrl = tk.Frame(main, bg=PANEL, width=330)
        ctrl.pack(side="left", fill="y", padx=(0, 12))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_canvas(right)

        # ── Formula strip below everything ────────────────────────────────────
        self._build_formula_bar()

    def _build_controls(self, parent):
        tk.Label(parent, text="PARAMETERS",
                 font=("Courier", 12, "bold"), fg=TEXT, bg=PANEL).pack(pady=(18, 0))
        tk.Label(parent, text="live interference updates",
                 font=("Courier", 8), fg=SUBTEXT, bg=PANEL).pack()

        # ── Optics ─────────────────────────────────────────────────────────
        self._section(parent, "OPTICS")
        self._slider(parent, "Wavelength λ", self.lam,
                     380, 780, ACCENT, res=1, fmt="{:.0f}", unit=" nm")
        self._slider(parent, "Slit sep.  d", self.d,
                     0.05, 3.0, ACCENT2, res=0.01, fmt="{:.2f}", unit=" mm")
        self._slider(parent, "Screen dist L", self.L,
                     0.1, 3.0, GOOD, res=0.05, fmt="{:.2f}", unit=" m")

        # ── Path Difference ─────────────────────────────────────────────────
        self._section(parent, "PATH DIFFERENCE")
        self._slider(parent, "Δx  (path diff)", self.delta_x,
                     -5.0, 5.0, GOLD, res=0.05, fmt="{:.2f}", unit=" μm")

        # Live φ display
        self.phi_frame = tk.Frame(parent, bg="#07111f", pady=6, padx=10)
        self.phi_frame.pack(fill="x", padx=14, pady=(4, 0))
        tk.Label(self.phi_frame, text="φ = 2π·Δx / λ",
                 font=("Courier", 8, "bold"), fg=GOLD, bg="#07111f").pack()
        self.phi_lbl = tk.Label(self.phi_frame, text="φ = 0.0000 rad",
                                font=("Courier", 9), fg=GOLD, bg="#07111f")
        self.phi_lbl.pack()
        self.phi_sub = tk.Label(self.phi_frame,
                                text="= 2π·0.00/550 = 0.000 rad",
                                font=("Courier", 7), fg=SUBTEXT, bg="#07111f")
        self.phi_sub.pack()

        # ── Beam Intensities ────────────────────────────────────────────────
        self._section(parent, "BEAM INTENSITIES")
        self._slider(parent, "I₁  (Beam 1)", self.I1,
                     0.01, 2.0, ACCENT, res=0.01, fmt="{:.2f}", unit=" W")
        self._slider(parent, "I₂  (Beam 2)", self.I2,
                     0.01, 2.0, ACCENT2, res=0.01, fmt="{:.2f}", unit=" W")

        # ── Extra Effects ───────────────────────────────────────────────────
        self._section(parent, "EXTRA EFFECTS")
        self._slider(parent, "Coherence γ", self.coh,
                     0.0, 1.0, PURPLE, res=0.01, fmt="{:.2f}", unit="")
        self._slider(parent, "Tilt angle θ", self.theta,
                     -30, 30, RED, res=0.5, fmt="{:.1f}", unit="°")

        # ── Live Metrics ─────────────────────────────────────────────────────
        self._section(parent, "LIVE METRICS")
        self.vis_var    = tk.StringVar(value="—")
        self.fringe_var = tk.StringVar(value="—")
        self.order_var  = tk.StringVar(value="—")
        self.dx_var     = tk.StringVar(value="—")
        self.phi_var2   = tk.StringVar(value="—")
        self.shift_var  = tk.StringVar(value="—")

        metrics = [
            ("Visibility V",      self.vis_var,    GOOD),
            ("Fringe width β",    self.fringe_var, ACCENT),
            ("Bright orders ±N",  self.order_var,  ACCENT2),
            ("Path diff Δx",      self.dx_var,     GOLD),
            ("Phase φ",           self.phi_var2,   GOLD),
            ("Central max shift", self.shift_var,  PURPLE),
        ]
        for lbl, var, col in metrics:
            row = tk.Frame(parent, bg=HI, pady=4, padx=10)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=lbl, font=("Courier", 8),
                     fg=SUBTEXT, bg=HI).pack(side="left")
            tk.Label(row, textvariable=var,
                     font=("Courier", 10, "bold"), fg=col,
                     bg=HI).pack(side="right")

        # (Full formula reference is in the bottom bar)

        # ── Animation toggle ─────────────────────────────────────────────────
        self._section(parent, "ANIMATION")
        anim_row = tk.Frame(parent, bg=PANEL)
        anim_row.pack(fill="x", padx=14, pady=(4, 0))
        self.anim_btn = tk.Button(
            anim_row, text="▶  ANIMATE Δx",
            font=("Courier", 9, "bold"), fg=BG, bg=PURPLE,
            relief="flat", bd=0, pady=4, cursor="hand2",
            command=self._toggle_anim)
        self.anim_btn.pack(fill="x")

        self.anim_speed = tk.DoubleVar(value=0.08)
        speed_row = tk.Frame(parent, bg=PANEL, pady=2)
        speed_row.pack(fill="x", padx=14)
        tk.Label(speed_row, text="Anim speed",
                 font=("Courier", 9), fg=TEXT, bg=PANEL).pack(side="left")
        ttk.Scale(speed_row, from_=0.01, to=0.30,
                  variable=self.anim_speed, orient="horizontal",
                  length=140).pack(side="right")

        # (Reset is now in the top-right header bar)

    def _build_formula_bar(self):
        """Horizontal formula strip pinned to the bottom of the window."""
        bar = tk.Frame(self.root, bg="#07111f", pady=6)
        bar.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(bar, text="PHYSICS REFERENCE  ·",
                 font=("Courier", 8, "bold"), fg=ACCENT,
                 bg="#07111f").pack(side="left", padx=(12, 8))

        # Each formula block: title + formula side by side
        formulas = [
            ("Intensity",      "I = I₁ + I₂ + 2√(I₁I₂)·γ·cos(ky + φ)",  TEXT),
            ("Spatial freq",   "k = 2πd / (λL)",                           ACCENT),
            ("Phase",          "φ = 2π·Δx / λ",                            GOLD),
            ("Fringe width",   "β = λL / d",                               ACCENT2),
            ("Visibility",     "V = γ · 2√(I₁I₂) / (I₁+I₂)",             GOOD),
            ("Central max",    "y₀ = −φ / k = −ΔxL / d",                  PURPLE),
        ]

        for title, formula, col in formulas:
            cell = tk.Frame(bar, bg="#0d1526", padx=8, pady=3,
                            relief="flat", bd=0)
            cell.pack(side="left", padx=5)
            tk.Label(cell, text=title,
                     font=("Courier", 7), fg=SUBTEXT,
                     bg="#0d1526").pack(anchor="w")
            tk.Label(cell, text=formula,
                     font=("Courier", 8, "bold"), fg=col,
                     bg="#0d1526").pack(anchor="w")

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(10.5, 7.5), facecolor=BG)
        gs = GridSpec(2, 2, figure=self.fig,
                      hspace=0.46, wspace=0.34,
                      left=0.07, right=0.97, top=0.93, bottom=0.08)
        self.ax2d  = self.fig.add_subplot(gs[0, :])
        self.ax1d  = self.fig.add_subplot(gs[1, 0])
        self.ax_wl = self.fig.add_subplot(gs[1, 1])

        for ax in (self.ax2d, self.ax1d, self.ax_wl):
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values():
                sp.set_edgecolor(HI)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Physics
    # ─────────────────────────────────────────────────────────────────────────
    def _wavelength_to_rgb(self, wl_nm):
        w = wl_nm
        if   380 <= w < 440: r, g, b = (440-w)/(440-380), 0, 1
        elif 440 <= w < 490: r, g, b = 0, (w-440)/(490-440), 1
        elif 490 <= w < 510: r, g, b = 0, 1, (510-w)/(510-490)
        elif 510 <= w < 580: r, g, b = (w-510)/(580-510), 1, 0
        elif 580 <= w < 645: r, g, b = 1, (645-w)/(645-580), 0
        elif 645 <= w <= 780: r, g, b = 1, 0, 0
        else:                 r, g, b = 0.5, 0.5, 0.5
        return (r, g, b)

    def _compute(self):
        lam_nm  = self.lam.get()
        lam     = lam_nm * 1e-9            # m
        d       = self.d.get() * 1e-3      # m
        L       = self.L.get()             # m
        I1      = self.I1.get()
        I2      = self.I2.get()
        coh     = self.coh.get()
        theta   = np.deg2rad(self.theta.get())
        dx_um   = self.delta_x.get()       # μm
        dx_m    = dx_um * 1e-6             # m

        # ── Phase from path difference ─────────────────────────────────────
        phi = (2 * np.pi * dx_m) / lam    # radians

        # ── Fringe geometry ────────────────────────────────────────────────
        beta    = lam * L / d              # fringe width (m)
        k_fringe = 2 * np.pi * d / (lam * L)  # spatial frequency (rad/m)

        # ── Visibility ─────────────────────────────────────────────────────
        I_max = (np.sqrt(I1) + np.sqrt(I2))**2
        I_min = (np.sqrt(I1) - np.sqrt(I2))**2
        V_max = (I_max - I_min) / (I_max + I_min) if (I_max + I_min) > 0 else 0
        V     = coh * V_max

        # ── Centre-of-pattern shift due to φ ─────────────────────────────
        # Central max when k_fringe·y + phi = 0  → y_c = -phi/k_fringe
        y_central = -phi / k_fringe        # m
        # Tilt adds a further offset
        y_tilt    = -L * np.tan(theta)
        y_c_total = y_central + y_tilt

        # ── 1-D cross section ──────────────────────────────────────────────
        y    = np.linspace(-6*beta, 6*beta, 3000)
        arg  = k_fringe * (y - L * np.tan(theta)) + phi
        # Full interference formula: I = I1 + I2 + 2√(I1·I2)·γ·cos(arg)
        I1D  = I1 + I2 + 2*np.sqrt(I1*I2) * coh * np.cos(arg)
        # Gaussian envelope (finite slit width)
        sigma_env = 8 * beta
        env1d     = np.exp(-y**2 / (2*sigma_env**2))
        I1D       = I1D * env1d

        # ── 2-D pattern ───────────────────────────────────────────────────
        y2d = np.linspace(-6*beta, 6*beta, 500)
        x2d = np.linspace(-2*beta, 2*beta, 200)
        Y, X = np.meshgrid(y2d, x2d, indexing="ij")
        arg2d = k_fringe * (Y - L * np.tan(theta)) + phi
        I2D   = I1 + I2 + 2*np.sqrt(I1*I2) * coh * np.cos(arg2d)
        env2d = np.exp(-Y**2 / (2*sigma_env**2))
        I2D   = I2D * env2d

        n_orders = int(5)
        return (y, I1D, y2d, x2d, I2D,
                beta, V, n_orders,
                phi, dx_um, y_c_total)

    # ─────────────────────────────────────────────────────────────────────────
    # Render
    # ─────────────────────────────────────────────────────────────────────────
    def _update(self, *_):
        (y, I1D, y2d, x2d, I2D,
         beta, V, n_orders,
         phi, dx_um, y_central) = self._compute()

        lam_nm   = self.lam.get()
        rgb      = self._wavelength_to_rgb(lam_nm)
        beta_mm  = beta * 1e3
        y_c_mm   = y_central * 1e3

        # ── Update live labels ─────────────────────────────────────────────
        self.vis_var.set(f"{V:.4f}")
        self.fringe_var.set(f"{beta_mm:.3f} mm")
        self.order_var.set(f"± {n_orders}")
        self.dx_var.set(f"{dx_um:.3f} μm")
        self.phi_var2.set(f"{phi:.4f} rad")
        self.shift_var.set(f"{y_c_mm:.3f} mm")

        # Update φ formula box
        self.phi_lbl.config(text=f"φ = {phi:.4f} rad")
        self.phi_sub.config(
            text=f"= 2π·{dx_um:.2f}μm / {lam_nm:.0f}nm")

        # ── 2-D Fringe image ───────────────────────────────────────────────
        ax = self.ax2d
        ax.cla()
        ax.set_facecolor("#000")
        ext = [y2d[0]*1e3, y2d[-1]*1e3, x2d[0]*1e3, x2d[-1]*1e3]
        ax.imshow(I2D.T, aspect="auto", extent=ext, origin="lower",
                  cmap=FRINGE_CMAP, interpolation="bilinear")

        # Central maximum marker
        if abs(y_c_mm) <= y2d[-1]*1e3:
            ax.axvline(y_c_mm, color=GOLD, lw=1.2, ls="--", alpha=0.85)
            ax.text(y_c_mm + 0.1, x2d[-1]*1e3*0.75,
                    f"m=0\n{y_c_mm:.2f} mm",
                    color=GOLD, fontsize=7, va="top")

        ax.set_xlabel("Screen position y (mm)", fontsize=9)
        ax.set_ylabel("x (mm)", fontsize=9)
        ax.set_title(
            f"2-D Fringe Pattern  |  λ={lam_nm:.0f} nm  "
            f"d={self.d.get():.2f} mm  L={self.L.get():.2f} m  "
            f"Δx={dx_um:.2f} μm  φ={phi:.3f} rad  V={V:.3f}",
            color=TEXT, fontsize=9.5, pad=6)
        for sp in ax.spines.values():
            sp.set_edgecolor(HI)

        # ── 1-D Cross-section ──────────────────────────────────────────────
        ax1 = self.ax1d
        ax1.cla()
        ax1.set_facecolor(PANEL)
        ax1.grid(True, linestyle="--", alpha=0.35)

        ax1.fill_between(y*1e3, I1D, alpha=0.18, color=rgb)
        ax1.plot(y*1e3, I1D, color=rgb, lw=1.8)

        # Mark fringe width β
        I_peak = I1D.max()
        ax1.annotate("", xy=(y_c_mm + beta_mm/2, I_peak*0.90),
                     xytext=(y_c_mm - beta_mm/2, I_peak*0.90),
                     arrowprops=dict(arrowstyle="<->", color=ACCENT2, lw=1.5))
        ax1.text(y_c_mm, I_peak*0.94, f"β={beta_mm:.2f} mm",
                 color=ACCENT2, ha="center", fontsize=8)

        # Central maximum marker
        ax1.axvline(y_c_mm, color=GOLD, lw=1.3, ls="--", alpha=0.85,
                    label=f"m=0 @ {y_c_mm:.2f} mm")
        ax1.legend(fontsize=7, loc="upper right",
                   framealpha=0.25, labelcolor=GOLD)

        ax1.set_xlabel("Screen position y (mm)", fontsize=8)
        ax1.set_ylabel("Intensity (a.u.)", fontsize=8)
        ax1.set_title("1-D Intensity Cross-section", fontsize=9, color=TEXT)
        for sp in ax1.spines.values():
            sp.set_edgecolor(HI)

        # ── Visible spectrum bar ───────────────────────────────────────────
        ax2 = self.ax_wl
        ax2.cla()
        ax2.set_facecolor(PANEL)
        wl_arr    = np.linspace(380, 780, 500)
        colors_wl = [self._wavelength_to_rgb(w) for w in wl_arr]
        cmap_wl   = LinearSegmentedColormap.from_list(
            "visible", colors_wl, N=500)
        grad = np.linspace(0, 1, 256).reshape(1, -1)
        ax2.imshow(grad, aspect="auto", extent=[380, 780, 0, 1],
                   cmap=cmap_wl, origin="lower")
        ax2.axvline(lam_nm, color="white", lw=2.2, ls="--")
        ax2.text(lam_nm, 1.06, f"{lam_nm:.0f} nm",
                 color="white", ha="center", fontsize=9,
                 transform=ax2.get_xaxis_transform())
        ax2.set_xlabel("Wavelength (nm)", fontsize=8)
        ax2.set_yticks([])
        ax2.set_title("Visible Spectrum / Current λ", fontsize=9, color=TEXT)
        for sp in ax2.spines.values():
            sp.set_edgecolor(HI)

        self.canvas.draw_idle()

    # ─────────────────────────────────────────────────────────────────────────
    # Animation
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_anim(self):
        if self._anim_id is None:
            self._anim_running = True
            self.anim_btn.config(text="■  STOP ANIMATION", bg=RED)
            self._step_anim()
        else:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
            self.anim_btn.config(text="▶  ANIMATE Δx", bg=PURPLE)

    def _step_anim(self):
        step = self.anim_speed.get()
        val  = self.delta_x.get() + self._anim_dir * step
        if val >= 5.0:
            val = 5.0
            self._anim_dir = -1
        elif val <= -5.0:
            val = -5.0
            self._anim_dir = 1
        self.delta_x.set(round(val, 4))
        # _update is triggered automatically by trace; just schedule next
        self._anim_id = self.root.after(40, self._step_anim)

    # ─────────────────────────────────────────────────────────────────────────
    def _reset(self):
        if self._anim_id:
            self._toggle_anim()
        self.lam.set(550)
        self.d.set(0.5)
        self.L.set(1.0)
        self.I1.set(1.0)
        self.I2.set(1.0)
        self.coh.set(1.0)
        self.theta.set(0.0)
        self.delta_x.set(0.0)
        self._anim_dir = 1


def main():
    root = tk.Tk()
    FringePatternApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()