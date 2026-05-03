"""
Fringe Pattern Simulator — v2.1  (Bug-Fixed Enhanced 3D)
=========================================================
Fixes vs v2.0 (based on screenshot review):
  • y_central formula fixed: was mixing mm/m → now fully in metres throughout
  • 1-D plot β annotation and central-max line now correctly placed
  • 1-D plot fill/line colour matches current wavelength (not hardcoded green)
  • 3D screen texture: y→display mapping corrected, fringes appear at right positions
  • 3D wavefront rings: radius rescaled properly to Z_sc display space → visible arcs
  • 3D ±1 order rays: use correct physical β scaled to display coords
  • src_z NameError in tilt label fixed
  • Barrier slit_gap clamped so slits always remain open for any d value
  • Labels decluttered and repositioned in 3D view
  • β annotation on screen added in 3D
"""

import sys, ctypes, time
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
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D          # noqa (registers projection)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#080c14"
PANEL   = "#0d1120"
ACCENT  = "#00e5ff"
ACCENT2 = "#ff9f1c"
GOOD    = "#7fff7f"
PURPLE  = "#d4aaff"
RED     = "#ff6b6b"
TEXT    = "#dde4f0"
SUBTEXT = "#555e78"
HI      = "#1a2038"
SLBG    = "#141928"
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
    "grid.linewidth":   0.4,
    "font.family":      "monospace",
})

_fringe_colors = [
    (0.03, 0.05, 0.12),
    (0.10, 0.30, 0.75),
    (0.95, 0.98, 1.00),
    (0.10, 0.30, 0.75),
    (0.03, 0.05, 0.12),
]
FRINGE_CMAP = LinearSegmentedColormap.from_list("fringe", _fringe_colors, N=512)

PRESETS = [
    ("Standard DSE",      {"lam":550,"d":0.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
    ("Red Light",          {"lam":650,"d":0.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
    ("Blue Light",         {"lam":450,"d":0.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
    ("Partial Coherence",  {"lam":550,"d":0.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":0.5,"theta":0.0,"dx":0.0,"sig":8}),
    ("Tilted Beam",        {"lam":550,"d":0.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":1.0,"theta":15.0,"dx":0.0,"sig":8}),
    ("Unequal Beams",      {"lam":550,"d":0.5,"L":1.0,"I1":2.0,"I2":0.5,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
    ("Far Screen",         {"lam":550,"d":0.3,"L":2.5,"I1":1.0,"I2":1.0,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
    ("Wide Slits",         {"lam":550,"d":1.5,"L":1.0,"I1":1.0,"I2":1.0,"coh":1.0,"theta":0.0,"dx":0.0,"sig":8}),
]

TIPS = {
    "Wavelength λ":     "Optical wavelength (nm). Changes fringe colour and spacing β=λL/d.",
    "Slit sep.  d":    "Slit separation (mm). Smaller d → wider fringes.",
    "Screen dist L":   "Slit-to-screen distance (m). Larger L → wider fringes.",
    "Δx  (path diff)": "Path difference (μm). Shifts fringes: y₀ = −ΔxL/d.",
    "I₁  (Beam 1)":    "Beam 1 intensity. Imbalance reduces contrast.",
    "I₂  (Beam 2)":    "Beam 2 intensity. V = 2√(I₁I₂)/(I₁+I₂) × γ",
    "Coherence γ":     "Coherence [0,1]. γ=1 → sharp fringes. γ=0 → none.",
    "Tilt angle θ":    "Beam tilt (°). Shifts fringe pattern laterally.",
    "σ envelope (×β)": "Gaussian envelope width (×β). Controls visible fringes.",
    "Wave rings":       "Number of wavefront arcs per slit in 3D view.",
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
        tw.wm_overrideredirect(True); tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg="#151e38")
        tk.Frame(tw, bg=ACCENT, height=1).pack(fill="x")
        tk.Label(tw, text=text, font=("Courier", 8), fg=TEXT, bg="#151e38",
                 padx=10, pady=7, wraplength=300, justify="left").pack()
    def _hide(self):
        if self._win: self._win.destroy(); self._win = None


class FringePatternApp:
    _anim_id      = None
    _anim_dir     = 1
    _upd_id       = None
    _advanced     = True
    _wave_phase   = 0.0
    _wave_anim_id = None

    def __init__(self, root):
        self.root = root
        root.title("Fringe Pattern Simulator  ·  v2.1")
        root.configure(bg=BG)
        root.geometry("1440x900")
        root.resizable(True, True)

        self.lam     = tk.DoubleVar(value=550.0)
        self.d       = tk.DoubleVar(value=0.5)
        self.L       = tk.DoubleVar(value=1.0)
        self.I1      = tk.DoubleVar(value=1.0)
        self.I2      = tk.DoubleVar(value=1.0)
        self.coh     = tk.DoubleVar(value=1.0)
        self.theta   = tk.DoubleVar(value=0.0)
        self.delta_x = tk.DoubleVar(value=0.0)
        self.sigma_k = tk.DoubleVar(value=8.0)
        self.n_rings = tk.IntVar(value=12)
        self._adv_frames = []

        self._build_ui()
        self._update()
        self._start_wave_anim()
        root.bind("<Control-r>", lambda e: self._reset())
        root.bind("<Control-R>", lambda e: self._reset())

    # ── helpers ───────────────────────────────────────────────────────────────
    def _section(self, parent, text):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(fill="x", padx=14, pady=(14, 2))
        tk.Label(f, text=text, font=("Courier", 8, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Frame(f, bg=HI, height=1).pack(side="left", fill="x", expand=True, padx=(6,0))

    def _slider(self, parent, label, var, lo, hi, color,
                res=0.01, fmt="{:.2f}", unit=""):
        row = tk.Frame(parent, bg=PANEL, pady=2)
        row.pack(fill="x", padx=14)
        top = tk.Frame(row, bg=PANEL); top.pack(fill="x")
        lw = tk.Label(top, text=label, font=("Courier", 9), fg=TEXT, bg=PANEL)
        lw.pack(side="left")
        vl = tk.Label(top, text=fmt.format(var.get())+unit,
                      font=("Courier", 9, "bold"), fg=color, bg=PANEL, width=10)
        vl.pack(side="right")
        sl = ttk.Scale(row, from_=lo, to=hi, variable=var, orient="horizontal", length=270)
        sl.pack(fill="x")
        ticks = tk.Frame(row, bg=PANEL); ticks.pack(fill="x")
        tk.Label(ticks, text=f"{lo}", font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(side="left")
        tk.Label(ticks, text=f"{hi}", font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(side="right")

        def on(*_):
            vl.config(text=fmt.format(var.get())+unit)
            self._debounced_update()
        var.trace_add("write", on)

        s = ttk.Style(); s.theme_use("clam")
        s.configure("Horizontal.TScale", background=PANEL, troughcolor=SLBG, sliderthickness=13)
        if label in TIPS: ToolTip(lw, TIPS[label])
        return sl

    def _debounced_update(self, *_):
        if self._upd_id is not None:
            try: self.root.after_cancel(self._upd_id)
            except Exception: pass
        self._upd_id = self.root.after(25, self._update)

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=BG, pady=8); hdr.pack(fill="x", padx=22)
        tk.Label(hdr, text="FRINGE PATTERN SIMULATOR",
                 font=("Courier", 18, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(hdr, text="  ·  Young's Double-Slit  |  Real-Time 3D Wavefront",
                 font=("Courier", 10), fg=SUBTEXT, bg=BG).pack(side="left", pady=4)
        ab = tk.Frame(hdr, bg=BG); ab.pack(side="right")
        tk.Button(ab, text="📷 EXPORT", font=("Courier", 9, "bold"),
                  fg=BG, bg=PURPLE, relief="flat", bd=0, padx=10, pady=5,
                  cursor="hand2", command=self._export).pack(side="left", padx=(0,6))
        tk.Button(ab, text="⟳  RESET", font=("Courier", 10, "bold"),
                  fg=BG, bg=ACCENT, relief="flat", bd=0, padx=14, pady=5,
                  cursor="hand2", command=self._reset).pack(side="left")

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=14, pady=(0,4))
        ctrl = tk.Frame(main, bg=PANEL, width=310)
        ctrl.pack(side="left", fill="y", padx=(0,10))
        ctrl.pack_propagate(False)
        self._build_controls(ctrl)
        right = tk.Frame(main, bg=BG); right.pack(side="left", fill="both", expand=True)
        self._build_canvas(right)
        self._build_formula_bar()

    def _build_controls(self, p):
        tk.Label(p, text="PARAMETERS", font=("Courier", 11, "bold"), fg=TEXT, bg=PANEL).pack(pady=(16,0))
        tk.Label(p, text="live interference updates", font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack()

        self._section(p, "OPTICS")
        self._slider(p, "Wavelength λ", self.lam, 380, 780, ACCENT, res=1, fmt="{:.0f}", unit=" nm")
        self._slider(p, "Slit sep.  d", self.d, 0.05, 3.0, ACCENT2, fmt="{:.2f}", unit=" mm")
        self._slider(p, "Screen dist L", self.L, 0.1, 3.0, GOOD, fmt="{:.2f}", unit=" m")

        f_pd = tk.Frame(p, bg=PANEL); f_pd.pack(fill="x"); self._adv_frames.append(f_pd)
        self._section(f_pd, "PATH DIFFERENCE")
        self._slider(f_pd, "Δx  (path diff)", self.delta_x, -50.0, 50.0, GOLD, res=0.5, fmt="{:.1f}", unit=" μm")

        self.phi_frame = tk.Frame(p, bg="#06101c", pady=5, padx=8)
        self.phi_frame.pack(fill="x", padx=14, pady=(2,0))
        self._adv_frames.append(self.phi_frame)
        tk.Label(self.phi_frame, text="φ = 2π·Δx / λ", font=("Courier", 8, "bold"), fg=GOLD, bg="#06101c").pack()
        self.phi_lbl = tk.Label(self.phi_frame, text="φ = 0.0000 rad", font=("Courier", 8), fg=GOLD, bg="#06101c")
        self.phi_lbl.pack()

        self._section(p, "BEAM INTENSITIES")
        self._slider(p, "I₁  (Beam 1)", self.I1, 0.01, 2.0, ACCENT, fmt="{:.2f}", unit=" W")
        self._slider(p, "I₂  (Beam 2)", self.I2, 0.01, 2.0, ACCENT2, fmt="{:.2f}", unit=" W")

        self._section(p, "EXTRA EFFECTS")
        self._slider(p, "Coherence γ", self.coh, 0.0, 1.0, PURPLE, fmt="{:.2f}")
        self._slider(p, "Tilt angle θ", self.theta, -30, 30, RED, res=0.5, fmt="{:.1f}", unit="°")
        self._slider(p, "σ envelope (×β)", self.sigma_k, 1.0, 20.0, "#88ffcc", res=0.5, fmt="{:.1f}", unit="×β")

        self._section(p, "3D VISUALIZATION")
        self._slider(p, "Wave rings", self.n_rings, 4, 20, "#aaddff", res=1, fmt="{:.0f}")

        tog = tk.Frame(p, bg=PANEL); tog.pack(fill="x", padx=14, pady=(6,0))
        self._mode_btn = tk.Button(tog, text="▽  BEGINNER MODE",
                                   font=("Courier", 7, "bold"), fg=ACCENT, bg=HI,
                                   relief="flat", bd=0, pady=3, cursor="hand2",
                                   command=self._toggle_mode)
        self._mode_btn.pack(fill="x")

        self._section(p, "LIVE METRICS")
        self.vis_var    = tk.StringVar(value="—")
        self.fringe_var = tk.StringVar(value="—")
        self.dx_var     = tk.StringVar(value="—")
        self.phi_var2   = tk.StringVar(value="—")
        self.shift_var  = tk.StringVar(value="—")
        self.order_var  = tk.StringVar(value="—")
        for lbl, var, col in [
            ("Visibility V",      self.vis_var,    GOOD),
            ("Fringe width β",    self.fringe_var, ACCENT),
            ("Path diff Δx",      self.dx_var,     GOLD),
            ("Phase φ",           self.phi_var2,   GOLD),
            ("Central max shift", self.shift_var,  PURPLE),
            ("Bright orders ±N",  self.order_var,  ACCENT2),
        ]:
            r = tk.Frame(p, bg=HI, pady=3, padx=8); r.pack(fill="x", padx=14, pady=1)
            tk.Label(r, text=lbl, font=("Courier", 8), fg=SUBTEXT, bg=HI).pack(side="left")
            tk.Label(r, textvariable=var, font=("Courier", 9, "bold"), fg=col, bg=HI).pack(side="right")

        self._section(p, "ANIMATION")
        self.anim_btn = tk.Button(p, text="▶  ANIMATE Δx",
                                  font=("Courier", 9, "bold"), fg=BG, bg=PURPLE,
                                  relief="flat", bd=0, pady=4, cursor="hand2",
                                  command=self._toggle_anim)
        self.anim_btn.pack(fill="x", padx=14)
        sr = tk.Frame(p, bg=PANEL, pady=2); sr.pack(fill="x", padx=14)
        tk.Label(sr, text="Speed", font=("Courier", 8), fg=TEXT, bg=PANEL).pack(side="left")
        self.anim_speed = tk.DoubleVar(value=0.08)
        self.fps_lbl = tk.Label(sr, text="", font=("Courier", 7), fg=SUBTEXT, bg=PANEL)
        self.fps_lbl.pack(side="right")
        ttk.Scale(sr, from_=0.01, to=0.30, variable=self.anim_speed,
                  orient="horizontal", length=100).pack(side="right", padx=(0,4))

        self._section(p, "PRESETS")
        for name, vals in PRESETS:
            b = tk.Button(p, text=name, font=("Courier", 8), fg=TEXT, bg=HI,
                          relief="flat", bd=0, pady=2, cursor="hand2",
                          command=lambda v=vals: self._apply_preset(v))
            b.pack(fill="x", padx=14, pady=1)
            b.bind("<Enter>", lambda e, w=b: w.config(bg=ACCENT, fg=BG))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=HI, fg=TEXT))
        tk.Label(p, text="Ctrl+R → reset", font=("Courier", 7), fg=SUBTEXT, bg=PANEL).pack(pady=(4,10))

    def _build_formula_bar(self):
        bar = tk.Frame(self.root, bg="#05101e", pady=5)
        bar.pack(fill="x", padx=14, pady=(0,6))
        tk.Label(bar, text="PHYSICS  ·", font=("Courier", 8, "bold"),
                 fg=ACCENT, bg="#05101e").pack(side="left", padx=(10,8))
        for title, formula, col in [
            ("Intensity",    "I = I₁+I₂+2√(I₁I₂)·γ·cos(ky+φ)", TEXT),
            ("Fringe width", "β = λL / d",                        ACCENT2),
            ("Phase",        "φ = 2π·Δx / λ",                    GOLD),
            ("Visibility",   "V = γ·2√(I₁I₂)/(I₁+I₂)",          GOOD),
            ("Central max",  "y₀ = −ΔxL / d",                    PURPLE),
        ]:
            cell = tk.Frame(bar, bg="#0a1828", padx=8, pady=2); cell.pack(side="left", padx=4)
            tk.Label(cell, text=title, font=("Courier", 7), fg=SUBTEXT, bg="#0a1828").pack(anchor="w")
            tk.Label(cell, text=formula, font=("Courier", 8, "bold"), fg=col, bg="#0a1828").pack(anchor="w")

    def _build_canvas(self, parent):
        self.fig = plt.figure(figsize=(11, 7.8), facecolor=BG)
        gs = GridSpec(3, 2, figure=self.fig,
                      height_ratios=[3.8, 0.28, 3.8],
                      hspace=0.44, wspace=0.32,
                      left=0.06, right=0.97, top=0.94, bottom=0.07)
        self.ax2d  = self.fig.add_subplot(gs[0, :])
        self.ax_wl = self.fig.add_subplot(gs[1, :])
        self.ax1d  = self.fig.add_subplot(gs[2, 0])
        self.ax3d  = self.fig.add_subplot(gs[2, 1], projection="3d")
        for ax in (self.ax2d, self.ax1d, self.ax_wl):
            ax.set_facecolor(PANEL)
            for sp in ax.spines.values(): sp.set_edgecolor(HI)
        self.ax3d.set_facecolor("#00000a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Physics ────────────────────────────────────────────────────────────────
    def _wavelength_to_rgb(self, wl):
        w = wl
        if   380 <= w < 440: r,g,b = (440-w)/60,  0,            1
        elif 440 <= w < 490: r,g,b = 0,            (w-440)/50,  1
        elif 490 <= w < 510: r,g,b = 0,             1,           (510-w)/20
        elif 510 <= w < 580: r,g,b = (w-510)/70,   1,            0
        elif 580 <= w < 645: r,g,b = 1,            (645-w)/65,   0
        elif 645 <= w <= 780: r,g,b = 1,            0,            0
        else:                 r,g,b = 0.5,           0.5,          0.5
        return (r, g, b)

    def _compute(self):
        """All physical quantities in SI (metres). Returns y, I1D in metres."""
        lam_nm = self.lam.get()
        lam    = lam_nm * 1e-9          # m
        d      = self.d.get()  * 1e-3   # m
        L      = self.L.get()           # m
        I1     = self.I1.get()
        I2     = self.I2.get()
        coh    = self.coh.get()
        theta  = np.deg2rad(self.theta.get())
        dx_um  = self.delta_x.get()
        dx_m   = dx_um * 1e-6

        phi      = 2 * np.pi * dx_m / lam          # rad
        beta     = lam * L / d                      # m
        k_fringe = 2 * np.pi * d / (lam * L)       # rad/m

        I_max = (np.sqrt(I1)+np.sqrt(I2))**2
        I_min = (np.sqrt(I1)-np.sqrt(I2))**2
        V_max = (I_max-I_min)/(I_max+I_min) if (I_max+I_min)>0 else 0.0
        V     = coh * V_max

        # Central max: k*(y - L*tanθ) + φ = 0  →  y = L*tanθ - φ/k
        # φ/k = (2π·dx/λ) / (2π·d/(λL)) = dx·L/d  ✓ (in metres)
        y_central = L * np.tan(theta) - phi / k_fringe   # metres

        n_orders = 5

        y_half  = 6.0 * beta
        y       = np.linspace(-y_half, y_half, 3000)
        arg     = k_fringe * (y - L * np.tan(theta)) + phi
        sig_e   = self.sigma_k.get() * beta
        env1d   = np.exp(-y**2 / (2*sig_e**2))
        I1D     = (I1 + I2 + 2*np.sqrt(I1*I2)*coh*np.cos(arg)) * env1d

        y2d   = np.linspace(-y_half, y_half, 500)
        x2d   = np.linspace(-2*beta, 2*beta, 200)
        Y, X  = np.meshgrid(y2d, x2d, indexing="ij")
        arg2d = k_fringe*(Y - L*np.tan(theta)) + phi
        env2d = np.exp(-Y**2 / (2*sig_e**2))
        I2D   = (I1 + I2 + 2*np.sqrt(I1*I2)*coh*np.cos(arg2d)) * env2d

        return (y, I1D, y2d, x2d, I2D,
                beta, V, n_orders, phi, dx_um, y_central)

    # ── 3D Scene ───────────────────────────────────────────────────────────────
    def _draw_3d(self, ax, beta, V, phi, dx_um, y_central_m, rgb, I1D, y_m):
        ax.cla()
        ax.set_facecolor("#00000a")

        lam_nm  = self.lam.get()
        d_mm    = self.d.get()
        L_m     = self.L.get()
        theta_d = self.theta.get()
        theta_r = np.deg2rad(theta_d)
        coh     = self.coh.get()
        n_rings = int(self.n_rings.get())

        # ── Display space ─────────────────────────────────────────────────
        # plot-Z = propagation direction (0 = barrier, Z_sc = screen)
        # plot-X = horizontal transverse (same units as d_mm: millimetres)
        # plot-Y = vertical transverse
        Z_sc   = 60.0       # screen z in display units
        src_z  = -28.0      # source z in display units

        half_d    = d_mm / 2.0
        wall_span = max(7.0, d_mm * 3.5 + 2.0)
        wall_h    = wall_span * 0.50
        # slit opening strictly less than half_d so barrier never disappears
        slit_gap  = float(np.clip(min(half_d * 0.55, 0.7), 0.15, half_d * 0.90))

        sc_hw  = wall_span / 2.0   # screen half-width in display units
        sc_hh  = wall_h    / 2.0

        # Physical ↔ display x-coordinate mapping:
        #   Physical screen spans ±6β metres; mapped to ±sc_hw display units
        y_span_m = 6.0 * beta   # metres

        def phys_to_disp(y_phys):
            return float(y_phys) / y_span_m * sc_hw

        # ── 1. Barrier ────────────────────────────────────────────────────
        segs = [
            [[-wall_span/2,-wall_h/2,0],[-half_d-slit_gap/2,-wall_h/2,0],
             [-half_d-slit_gap/2,wall_h/2,0],[-wall_span/2,wall_h/2,0]],
            [[-half_d+slit_gap/2,-wall_h/2,0],[half_d-slit_gap/2,-wall_h/2,0],
             [half_d-slit_gap/2,wall_h/2,0],[-half_d+slit_gap/2,wall_h/2,0]],
            [[half_d+slit_gap/2,-wall_h/2,0],[wall_span/2,-wall_h/2,0],
             [wall_span/2,wall_h/2,0],[half_d+slit_gap/2,wall_h/2,0]],
        ]
        ax.add_collection3d(Poly3DCollection(
            segs, facecolors="#0e1830", linewidths=0.8,
            edgecolors="#2a3a5e", alpha=0.95))
        # Slit glow lines
        for xc in [-half_d, half_d]:
            for xs in [xc-slit_gap/2, xc+slit_gap/2]:
                ax.plot([xs, xs], [-wall_h/2, wall_h/2], [0, 0],
                        color=rgb, lw=0.9, alpha=0.75)

        # ── 2. Incident laser beams ───────────────────────────────────────
        tilt_x = src_z * np.tan(theta_r)
        for sx in [-half_d, half_d]:
            ax.plot([tilt_x+sx, sx], [0,0], [src_z, 0],
                    color=rgb, lw=1.5, alpha=0.50)
        ax.scatter([tilt_x], [0], [src_z], c=[rgb], s=90, alpha=0.9, zorder=6)
        ax.text(tilt_x, 0, src_z-4, "SOURCE",
                color=rgb, fontsize=5.5, ha="center", va="top", alpha=0.8)
        if abs(theta_d) > 0.5:
            ax.text(tilt_x, 0, src_z+3, f"θ={theta_d:.1f}°",
                    color=RED, fontsize=5.5, ha="center")

        # ── 3. Wavefront rings ────────────────────────────────────────────
        # n_rings arcs per slit, spaced evenly across Z=[0, Z_sc].
        # _wave_phase animates them so they appear to travel forward.
        t_arc     = np.linspace(-np.pi/2.1, np.pi/2.1, 100)
        ring_step = Z_sc / n_rings   # display-unit spacing between rings

        for sx in [-half_d, half_d]:
            for ri in range(n_rings):
                frac  = (ri + self._wave_phase/(2*np.pi)) % n_rings
                r     = (frac + 0.3) * ring_step
                if r <= 0 or r > Z_sc * 1.05:
                    continue
                fade = max(0.05, 0.70 * (1.0 - r/(Z_sc*1.05)))
                xw = sx + r * np.sin(t_arc)
                zw =      r * np.cos(t_arc)
                yw = np.zeros_like(xw)
                mask = zw >= 0
                ax.plot(xw[mask], yw[mask], zw[mask],
                        color=rgb, lw=0.75, alpha=float(fade * coh))

        # ── 4. Screen backdrop ────────────────────────────────────────────
        sf = [[[-sc_hw,-sc_hh,Z_sc],[sc_hw,-sc_hh,Z_sc],
                [sc_hw,sc_hh,Z_sc],[-sc_hw,sc_hh,Z_sc]]]
        ax.add_collection3d(Poly3DCollection(
            sf, facecolors="#050c1a", linewidths=0.8,
            edgecolors="#1e2f50", alpha=0.75))

        # ── 5. Intensity texture on screen ────────────────────────────────
        # Sub-sample physical y array → display x coords
        step    = 4
        ys_sub  = y_m[::step]
        I_sub   = I1D[::step]
        I_norm  = I_sub / (I_sub.max() + 1e-12)
        x_d     = np.array([phys_to_disp(yv) for yv in ys_sub])
        bw      = abs(x_d[1]-x_d[0]) * 1.1 if len(x_d) > 1 else 0.05

        for xi, Iv in zip(x_d, I_norm):
            if Iv < 0.025: continue
            c_a = float(np.clip(Iv * 0.90, 0, 0.90))
            c_b = tuple(min(1.0, v*(0.4+0.6*Iv)) for v in rgb)
            verts = [[[xi-bw/2,-sc_hh,Z_sc],[xi+bw/2,-sc_hh,Z_sc],
                       [xi+bw/2, sc_hh,Z_sc],[xi-bw/2, sc_hh,Z_sc]]]
            ax.add_collection3d(Poly3DCollection(
                verts, facecolors=[c_b], linewidths=0, edgecolors="none", alpha=c_a))

        # ── 6. Rays: m=0 (solid) and m=±1 (dashed) ───────────────────────
        xc   = float(np.clip(phys_to_disp(y_central_m),          -sc_hw*0.95, sc_hw*0.95))
        xp1  = float(np.clip(phys_to_disp(y_central_m + beta),    -sc_hw*0.95, sc_hw*0.95))
        xm1  = float(np.clip(phys_to_disp(y_central_m - beta),    -sc_hw*0.95, sc_hw*0.95))

        for sx in [-half_d, half_d]:
            ax.plot([sx, xc], [0,0], [0, Z_sc], color=rgb, lw=1.5, alpha=0.85)
        ax.scatter([xc], [0], [Z_sc], c=[GOLD], s=55, alpha=0.95, zorder=7)

        for xb in [xp1, xm1]:
            for sx in [-half_d, half_d]:
                ax.plot([sx, xb], [0,0], [0, Z_sc],
                        color=rgb, lw=0.8, alpha=max(0.05, 0.35*coh), ls="--")

        # ── 7. Path difference annotation ────────────────────────────────
        if abs(dx_um) > 0.5:
            mid_z  = Z_sc * 0.5
            ext    = float(np.clip(abs(dx_um) * 0.04, 0.3, sc_hw * 0.20))
            sign   = 1 if dx_um > 0 else -1
            ax.plot([half_d, half_d + sign*ext], [0,0], [mid_z, mid_z],
                    color=GOLD, lw=1.5, alpha=0.90)
            ax.text(half_d + sign*(ext+0.3), 0, mid_z,
                    f"Δx={dx_um:.1f}μm\nφ={phi:.2f}rad",
                    color=GOLD, fontsize=5.5, va="center")

        # ── 8. Labels & annotations ───────────────────────────────────────
        y_c_mm  = y_central_m * 1e3
        beta_mm = beta * 1e3

        ax.text(-half_d, wall_h/2+0.9, 0, "S₁", color=ACCENT, fontsize=7, ha="center", va="bottom")
        ax.text( half_d, wall_h/2+0.9, 0, "S₂", color=ACCENT, fontsize=7, ha="center", va="bottom")
        ax.plot([-half_d, half_d], [wall_h/2+0.3]*2, [0,0], color=ACCENT2, lw=1.0, alpha=0.7)
        ax.text(0, wall_h/2+1.2, 0, f"d={d_mm:.2f}mm", color=ACCENT2, fontsize=5.5, ha="center")

        ax.plot([sc_hw+0.7]*2, [0,0], [0, Z_sc], color=GOOD, lw=0.8, alpha=0.55)
        ax.text(sc_hw+0.7, 0, Z_sc/2, f"  L={L_m:.2f}m", color=GOOD, fontsize=5.5, va="center")

        ax.text(-sc_hw-0.4, 0,  2, f"λ={lam_nm:.0f}nm", color=rgb,   fontsize=6, ha="right")
        coh_col = GOOD if coh>=0.9 else GOLD if coh>=0.5 else RED
        ax.text(-sc_hw-0.4, 0, -3, f"γ={coh:.2f}",      color=coh_col, fontsize=6, ha="right")

        vis_col = GOOD if V>=0.8 else GOLD if V>=0.4 else RED
        ax.text(0, -sc_hh-2, Z_sc/2, f"V = {V:.3f}",
                color=vis_col, fontsize=7, ha="center", fontweight="bold")
        ax.text(xc, 0, Z_sc+1.5, f"m=0\n{y_c_mm:.1f}mm",
                color=GOLD, fontsize=5.5, ha="center", va="bottom")

        # β bracket on screen
        beta_d = abs(xp1 - xc)
        if beta_d > 0.25:
            ax.plot([xc, xp1], [sc_hh+0.4]*2, [Z_sc, Z_sc], color=ACCENT2, lw=1.0, alpha=0.7)
            ax.text((xc+xp1)/2, sc_hh+1.1, Z_sc, f"β={beta_mm:.2f}mm",
                    color=ACCENT2, fontsize=5.5, ha="center")

        ax.text(0, -sc_hh-1.0, Z_sc, "SCREEN",  color=SUBTEXT, fontsize=5, ha="center", va="top")
        ax.text(0, -wall_h/2-1.0, 0, "BARRIER", color=SUBTEXT, fontsize=5, ha="center", va="top")

        # ── 9. View ───────────────────────────────────────────────────────
        ax.set_xlim(-wall_span/2-1.5, wall_span/2+1.5)
        ax.set_ylim(-wall_h/2-1.5,    wall_h/2+1.5)
        ax.set_zlim(-32, Z_sc+8)
        ax.set_axis_off()
        ax.set_title(
            f"3D Wavefront Propagation  |  "
            f"λ={lam_nm:.0f}nm  d={d_mm:.2f}mm  L={L_m:.2f}m  "
            f"θ={theta_d:.1f}°  V={V:.3f}",
            color=TEXT, fontsize=8.5, pad=-6)
        ax.view_init(elev=22, azim=-58)

    # ── Full render ────────────────────────────────────────────────────────────
    def _update(self, *_):
        self._upd_id = None
        (y, I1D, y2d, x2d, I2D,
         beta, V, n_orders,
         phi, dx_um, y_central) = self._compute()

        lam_nm  = self.lam.get()
        rgb     = self._wavelength_to_rgb(lam_nm)
        beta_mm = beta * 1e3
        y_c_mm  = y_central * 1e3

        self.vis_var.set(f"{V:.4f}")
        self.fringe_var.set(f"{beta_mm:.3f} mm")
        self.dx_var.set(f"{dx_um:.3f} μm")
        self.phi_var2.set(f"{phi:.4f} rad")
        self.shift_var.set(f"{y_c_mm:.3f} mm")
        self.order_var.set(f"± {n_orders}")
        self.phi_lbl.config(text=f"φ={phi:.4f} rad  (2π·{dx_um:.2f}/{lam_nm:.0f}nm)")

        # 2-D
        ax = self.ax2d; ax.cla(); ax.set_facecolor("#000")
        ext = [y2d[0]*1e3, y2d[-1]*1e3, x2d[0]*1e3, x2d[-1]*1e3]
        ax.imshow(I2D.T, aspect="auto", extent=ext, origin="lower",
                  cmap=FRINGE_CMAP, interpolation="bilinear")
        if abs(y_c_mm) <= y2d[-1]*1e3:
            ax.axvline(y_c_mm, color=GOLD, lw=1.2, ls="--", alpha=0.85)
            ax.text(y_c_mm+0.1, x2d[-1]*1e3*0.72,
                    f"m=0\n{y_c_mm:.2f}mm", color=GOLD, fontsize=7, va="top")
        ax.set_xlabel("Screen position y (mm)", fontsize=8)
        ax.set_ylabel("x (mm)", fontsize=8)
        ax.set_title(
            f"2-D Fringe Pattern  |  λ={lam_nm:.0f}nm  d={self.d.get():.2f}mm  "
            f"L={self.L.get():.2f}m  Δx={dx_um:.2f}μm  φ={phi:.3f}rad  V={V:.3f}",
            color=TEXT, fontsize=9, pad=5)
        for sp in ax.spines.values(): sp.set_edgecolor(HI)

        # 1-D — colour matches wavelength
        ax1 = self.ax1d; ax1.cla(); ax1.set_facecolor(PANEL)
        ax1.grid(True, linestyle="--", alpha=0.25)
        y_mm = y * 1e3
        ax1.fill_between(y_mm, I1D, alpha=0.20, color=rgb)
        ax1.plot(y_mm, I1D, color=rgb, lw=1.7)
        I_peak = I1D.max()
        ax1.annotate("",
                     xy    =(y_c_mm+beta_mm/2, I_peak*0.88),
                     xytext=(y_c_mm-beta_mm/2, I_peak*0.88),
                     arrowprops=dict(arrowstyle="<->", color=ACCENT2, lw=1.4))
        ax1.text(y_c_mm, I_peak*0.93, f"β={beta_mm:.2f}mm",
                 color=ACCENT2, ha="center", fontsize=8)
        ax1.axvline(y_c_mm, color=GOLD, lw=1.3, ls="--", alpha=0.85,
                    label=f"m=0 @ {y_c_mm:.2f}mm")
        ax1.legend(fontsize=7, loc="upper right", framealpha=0.2, labelcolor=GOLD)
        ax1.set_xlabel("Screen position y (mm)", fontsize=8)
        ax1.set_ylabel("Intensity (a.u.)", fontsize=8)
        ax1.set_title("1-D Intensity Cross-section", fontsize=9, color=TEXT)
        for sp in ax1.spines.values(): sp.set_edgecolor(HI)

        # Spectrum bar
        ax2 = self.ax_wl; ax2.cla(); ax2.set_facecolor(PANEL)
        wl_arr = np.linspace(380, 780, 500)
        cmap_wl = LinearSegmentedColormap.from_list(
            "vis", [self._wavelength_to_rgb(w) for w in wl_arr], N=500)
        ax2.imshow(np.linspace(0,1,256).reshape(1,-1),
                   aspect="auto", extent=[380,780,0,1], cmap=cmap_wl, origin="lower")
        ax2.axvline(lam_nm, color="white", lw=2.0, ls="--")
        ax2.text(lam_nm, 1.05, f"{lam_nm:.0f}nm", color="white", ha="center",
                 fontsize=9, transform=ax2.get_xaxis_transform())
        ax2.set_xlabel("Wavelength (nm)", fontsize=8); ax2.set_yticks([])
        ax2.set_title("Visible Spectrum / Current λ", fontsize=8.5, color=TEXT)
        for sp in ax2.spines.values(): sp.set_edgecolor(HI)

        # 3-D
        self._draw_3d(self.ax3d, beta, V, phi, dx_um, y_central, rgb, I1D, y)
        self.canvas.draw_idle()

    # ── Wavefront animation loop ───────────────────────────────────────────────
    def _start_wave_anim(self):
        def _tick():
            self._wave_phase = (self._wave_phase + 0.20) % (2*np.pi)
            (y, I1D, _, _, _, beta, V, _, phi, dx_um, yc) = self._compute()
            rgb = self._wavelength_to_rgb(self.lam.get())
            self._draw_3d(self.ax3d, beta, V, phi, dx_um, yc, rgb, I1D, y)
            self.canvas.draw_idle()
            self._wave_anim_id = self.root.after(80, _tick)
        self._wave_anim_id = self.root.after(300, _tick)

    # ── Δx animation ──────────────────────────────────────────────────────────
    def _toggle_anim(self):
        if self._anim_id is None:
            self.anim_btn.config(text="■  STOP ANIMATION", bg=RED)
            self._step_anim()
        else:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
            self.anim_btn.config(text="▶  ANIMATE Δx", bg=PURPLE)

    def _step_anim(self):
        t0 = time.perf_counter()
        step = self.anim_speed.get()
        val  = self.delta_x.get() + self._anim_dir * step
        if   val >= 50.0:  val = 50.0;  self._anim_dir = -1
        elif val <= -50.0: val = -50.0; self._anim_dir =  1
        self.delta_x.set(round(val, 4))
        fps = 1.0 / max(time.perf_counter()-t0+0.040, 0.001)
        self.fps_lbl.config(text=f"{fps:.0f} fps")
        self._anim_id = self.root.after(40, self._step_anim)

    # ── Misc ───────────────────────────────────────────────────────────────────
    def _reset(self):
        if self._anim_id: self._toggle_anim()
        self.lam.set(550); self.d.set(0.5);  self.L.set(1.0)
        self.I1.set(1.0);  self.I2.set(1.0); self.coh.set(1.0)
        self.theta.set(0.0); self.delta_x.set(0.0); self.sigma_k.set(8.0)
        self.n_rings.set(12); self._anim_dir = 1
        self.fps_lbl.config(text="")

    def _toggle_mode(self):
        self._advanced = not self._advanced
        if self._advanced:
            self._mode_btn.config(text="▽  BEGINNER MODE")
            for w in self._adv_frames: w.pack(fill="x")
        else:
            self._mode_btn.config(text="△  ADVANCED MODE")
            for w in self._adv_frames: w.pack_forget()

    def _apply_preset(self, v):
        if self._anim_id: self._toggle_anim()
        self.lam.set(v["lam"]); self.d.set(v["d"]);   self.L.set(v["L"])
        self.I1.set(v["I1"]);   self.I2.set(v["I2"]); self.coh.set(v["coh"])
        self.theta.set(v["theta"]); self.delta_x.set(v["dx"]); self.sigma_k.set(v["sig"])

    def _export(self):
        path = filedialog.asksaveasfilename(
            title="Export plot", defaultextension=".png",
            filetypes=[("PNG","*.png"),("PDF","*.pdf"),("SVG","*.svg")])
        if path:
            self.fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)


def main():
    root = tk.Tk()
    FringePatternApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()