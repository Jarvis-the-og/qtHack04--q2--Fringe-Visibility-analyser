# Fringe Visibility Analyzer — Project Analysis & Improvement Plan

> Written: 2026-05-02  
> Scope: Full codebase audit of all 4 Python source files + README, followed by a concrete roadmap for UX improvements and new features.

---

## Part 1 — Project Analysis & Simulator Summaries

### 1.1 High-Level Architecture

The project is a **multi-window Python/Tkinter + Matplotlib desktop application**. It follows a clean hub-and-spoke pattern:

```
launcher.py  (hub)
    ├── subprocess.Popen → two_beams_variation.py   (Module 01)
    ├── subprocess.Popen → fringe_pattern.py         (Module 02)
    └── subprocess.Popen → visibility_vs_intensity.py (Module 03)
```

Each module is **entirely self-contained** — its own Tk root, own Matplotlib figure, own colour palette constants, and own slider-to-physics-to-render pipeline. No shared state, no IPC. Modules run concurrently as independent OS processes.

**Shared design language across all files:**
- Dark background (`#0b0d17` / `#0c0d14` / `#0b0e18`) with coloured accents
- Monospace (`Courier`) font throughout
- `ttk.Scale` sliders with `trace_add("write", callback)` for live reactivity
- Matplotlib embedded via `FigureCanvasTkAgg` + `canvas.draw_idle()` on every update
- Three-zone layout: **header strip | left control panel | right plot area**

---

### 1.2 Launcher (`launcher.py`) — 413 lines

**Purpose:** Central hub / landing page. Does NOT do any physics; it is purely a navigation and documentation layer.

**Layout:** Scrollable single-page layout built on `tk.Canvas` + `ttk.Scrollbar`. Content is a `tk.Frame` embedded via `create_window`. Responsive: on `<Configure>` the content column is clamped to `CONTENT_MAX_W = 980 px` and centred. All text widgets call `reflow(available_width)` to recompute `wraplength`.

**Sections rendered:**

| Section | Widget class | Notes |
|---|---|---|
| Header | plain `tk.Label` | Title + subtitle |
| BACKGROUND | `TheoryBlock` × 2 | Fringe visibility theory + intensity formula |
| SIMULATION MODULES | `ModuleRow` × 3 | Number badge, title, description, Launch ▶ button |
| Footer | plain `tk.Label` | Keyboard hint + version string `v1.0` |

**Key compound widgets:**
- `SectionHeading` — all-caps label + 1 px rule
- `TheoryBlock` — 2 px accent bar on left + heading + body text
- `ModuleRow` — accent stripe, badge, divider, text column, launch button with hover swap

**Module launch mechanism:** `subprocess.Popen([sys.executable, path])`. Checks file existence first and shows `messagebox.showerror` if missing.

**Keyboard bindings:** `F11` full-screen toggle, `Escape` exit full-screen, MouseWheel / Button-4 / Button-5 scroll.

**Strengths:** Clean visual hierarchy, responsive reflow, correct cross-platform mouse-wheel handling.  
**Weaknesses:** No process status monitoring (can't tell if a launched module crashed), no loading indicator, version hardcoded as `v1.0`.

---

### 1.3 Module 01 — Two Beams Variation (`two_beams_variation.py`) — 307 lines

**Purpose:** Visualise two-beam interference at the waveform level. Shows individual beam profiles + their superposition in real time.

**Parameters (4 sliders):**

| Slider | Range | Default | Physical meaning |
|---|---|---|---|
| I₁ (Beam 1) | 0.01 – 2.00 W | 1.00 | Intensity of beam 1 |
| I₂ (Beam 2) | 0.01 – 2.00 W | 1.00 | Intensity of beam 2 |
| Phase Δφ | 0 – 360 ° | 0 | Relative phase offset |
| Freq k | 1.0 – 12.0 | 4.0 | Spatial frequency |

**Physics implemented:**
```
I_combined = I1 + I2 + 2·√(I1·I2)·cos(k·x + Δφ)
I_beam1    = I1·(1 + cos(k·x))
I_beam2    = I2·(1 + cos(k·x + Δφ))
I_max      = (√I1 + √I2)²
I_min      = (√I1 − √I2)²
V          = (I_max − I_min) / (I_max + I_min)
```

**Plots (3 axes via 2×2 GridSpec, top row merged):**
- **Top (merged):** Combined intensity `I(x)` — line + fill + `axhline` markers for `I_max`/`I_min` + faint fringe `imshow` overlay at 6% alpha
- **Bottom-left:** Beam 1 individual profile (cyan)
- **Bottom-right:** Beam 2 individual profile (orange)

**Live metrics panel:** Visibility V, I_max, I_min, I₁/I₂ ratio. A static formula box shows the interference equation. Reset button included.

**Notable patch applied:** Removes a spurious `+np.pi/4` hardcoded offset on Beam 2's profile that caused visual inconsistency.

**Strengths:** Clean, simple, great first introduction to interference.  
**Weaknesses:** No animation, no export, fixed x-domain (0 to 2π only), no way to compare scenarios, no tooltips.

---

### 1.4 Module 02 — Fringe Pattern Simulator (`fringe_pattern.py`) — 530 lines

**Purpose:** Full Young's double-slit experiment simulator. Most physically complete module, with 9 sliders + animation.

**Parameters (9 sliders + animation speed):**

| Slider | Range | Default | Physical meaning |
|---|---|---|---|
| Wavelength λ | 380 – 780 nm | 550 nm | Optical wavelength |
| Slit sep. d | 0.05 – 3.00 mm | 0.50 mm | Slit separation |
| Screen dist L | 0.10 – 3.00 m | 1.00 m | Screen distance |
| Δx (path diff) | −50 – 50 μm | 0 | Path difference |
| I₁ (Beam 1) | 0.01 – 2.00 W | 1.00 | Beam 1 intensity |
| I₂ (Beam 2) | 0.01 – 2.00 W | 1.00 | Beam 2 intensity |
| Coherence γ | 0.00 – 1.00 | 1.00 | Temporal/spatial coherence |
| Tilt angle θ | −30 – 30 ° | 0 | Beam tilt |
| Anim speed | 0.01 – 0.30 | 0.08 | Step size per animation frame |

**Physics implemented:**
```
k   = 2πd / (λL)
φ   = 2π·Δx / λ
β   = λL / d
y₀  = −φ / k
I   = [I₁+I₂+2√(I₁I₂)·γ·cos(k·(y − L·tanθ) + φ)] · exp(−y²/2σ²)   σ=8β
V   = γ · 2√(I₁I₂) / (I₁+I₂)
```

**Plots (3 axes via 2×2 GridSpec, top merged):**
- **Top (merged):** 2-D fringe image with custom blue-white-blue `FRINGE_CMAP` + gold dashed central-max marker
- **Bottom-left:** 1-D intensity cross-section with β arrow annotation + central-max marker
- **Bottom-right:** Visible spectrum bar (380–780 nm gradient) with cursor at current λ

**Live metrics:** V, β (mm), ±N orders, Δx (μm), φ (rad), central max shift (mm)

**Animation system:** `root.after(40, _step_anim)` at ~25 fps. Δx bounces between ±50 μm. Button toggles purple ▶ / red ■. Slider `trace_add` auto-triggers `_update()`.

**Formula strip:** Six physics formulas in a pinned bottom bar as colour-coded cells.

**Strengths:** Richest physics, beautiful wavelength colour rendering, formula strip is excellent reference, animation is highly engaging.  
**Weaknesses:** Heaviest computation per frame (500×3000 2-D grid every 40 ms). No exposed control for the Gaussian envelope width. Spectrum bar is small at default window size. 9 sliders is overwhelming for beginners.

---

### 1.5 Module 03 — Visibility vs Intensity Ratio (`visibility_vs_intensity.py`) — 418 lines

**Purpose:** Analytic exploration of `V = 2√r/(1+r)`, complemented by a phasor diagram and 2-D visibility heat-map.

**Parameters (4 sliders):**

| Slider | Range | Default | Physical meaning |
|---|---|---|---|
| I₁ (Beam 1) | 0.01 – 5.00 W | 1.00 | Sets r numerator |
| I₂ (Beam 2) | 0.01 – 5.00 W | 1.00 | Sets r denominator |
| Phase Δφ | 0 – 360 ° | 0 | Affects phasor diagram only |
| X-axis max r | 2.0 – 50.0 | 10.0 | Zoom on the V vs r curve |

**Physics implemented:**
```
r    = I₁ / I₂
V    = 2√r / (1 + r)
Imax = (√I₁ + √I₂)²
Imin = (√I₁ − √I₂)²
```

**Plots (3 axes via 2×2 GridSpec, top merged):**
- **Top (merged):** V vs r analytic curve with quality-zone colour shading + live hot-pink scatter marker + crosshairs + text annotation
- **Bottom-left:** Phasor diagram on polar axes — E₁ at 0°, E₂ at Δφ, resultant |E| dashed
- **Bottom-right:** 2-D visibility heat-map over I₁ × I₂ space (`plasma` colormap) with white V=1 diagonal and live cursor

**Fringe quality badge:** EXCELLENT / GOOD / MODERATE / POOR with matching colour, updates dynamically.

**Three patches applied:**
1. Phasor labels now use polar coordinate offsets (previously rendered off-screen)
2. Window enlarged to 1440×860 to prevent heatmap clipping
3. Colorbar stored as `self._cbar`, removed before re-creation to prevent stacking

**Strengths:** Powerful analytic overview, heat-map is pedagogically very strong, phasor gives intuitive electric-field picture.  
**Weaknesses:** Colorbar still recreated every frame (minor performance cost). Phase slider label doesn't clarify it only affects the phasor. Phasor draws on polar axes in a partially non-standard way that can cause visual glitches at extreme values.

---

## Part 2 — Identified Pain Points

### UX / Usability Issues

| # | Issue | Module(s) | Severity |
|---|---|---|---|
| U1 | No tooltips anywhere — sliders have no hover explanation | All | High |
| U2 | No preset/scenario buttons (e.g., "Equal beams", "4:1 ratio") | All | High |
| U3 | No export — users cannot save plots as images | All | High |
| U4 | Phase slider in M03 affects only the phasor, not labelled as such | M03 | Medium |
| U5 | Launcher shows no indication that launched modules are running | Launcher | Medium |
| U6 | No keyboard shortcut to reset sliders in module windows | All | Medium |
| U7 | 9 sliders in M02 is overwhelming for new users — no beginner/advanced mode | M02 | Medium |
| U8 | No zoom/pan on plots (Matplotlib toolbar not shown) | All | Low |
| U9 | Module windows open at fixed pixel sizes — small on high-DPI displays | All | Low |
| U10 | No dark/light theme toggle | All | Low |

### Performance Issues

| # | Issue | Module(s) | Severity |
|---|---|---|---|
| P1 | M02 recomputes a 500×3000 2-D array + 3000-point 1-D on every slider tick | M02 | High |
| P2 | M03 recreates `make_axes_locatable` + colorbar on every frame | M03 | Medium |
| P3 | No debounce on slider callbacks — rapid dragging fires many renders | All | Medium |
| P4 | Full `ax.cla()` + redraw on every update is expensive | All | Low |

### Code Quality Issues

| # | Issue | Module(s) |
|---|---|---|
| C1 | Colour constants duplicated across all 4 files (no shared `theme.py`) | All |
| C2 | `_add_slider` / `_slider` helper re-implemented differently in each module | All |
| C3 | Module 03 phasor mixes polar plot API with manual Cartesian math | M03 |
| C4 | Version string `v1.0` hardcoded in launcher footer | Launcher |

---

## Part 3 — Improvement Plan

### Phase 1 — UX Quick Wins (High Impact, Low Effort)

#### 1.1 Tooltip System
Add a lightweight `ToolTip` class (pure Tkinter `Toplevel`) wired to every slider label.
Each slider gets a 1–2 sentence explanation of what the parameter does physically.

```
Example — "Coherence γ":
"Temporal/spatial coherence factor. γ=1 → fully coherent (perfect fringes).
γ=0 → incoherent (no fringes at all). Simulates finite source size or path-length spread."
```

**Files:** `two_beams_variation.py`, `fringe_pattern.py`, `visibility_vs_intensity.py`  
**Effort:** ~3 hours

---

#### 1.2 Preset / Scenario Buttons
Add a `PRESETS` section in each module's control panel with 3–4 named scenario buttons.

**Module 01 presets:**
- Equal Beams (I₁=I₂=1, Δφ=0, k=4)
- Phase Opposition (Δφ=180° — dark fringes at centre)
- 4:1 Intensity Ratio (I₁=2, I₂=0.5)
- High Frequency (k=10)

**Module 02 presets:**
- Standard DSE (all defaults)
- Red Light (λ=650 nm)
- Blue Light (λ=450 nm)
- Partial Coherence (γ=0.5)
- Tilted Beam (θ=15°)

**Module 03 presets:**
- Perfect Balance (r=1, both I=1)
- 4:1 Ratio (I₁=2, I₂=0.5)
- 9:1 Ratio (I₁=4.5, I₂=0.5)
- Zoom Out (r_max=50)

**Files:** All three module files  
**Effort:** ~2 hours

---

#### 1.3 Export Plot Button
Add a `📷 SAVE PLOT` button in each module that calls `fig.savefig()` via `filedialog.asksaveasfilename` with PNG / PDF / SVG options.

```python
from tkinter import filedialog
def _export(self):
    path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG image","*.png"),("PDF","*.pdf"),("SVG","*.svg")]
    )
    if path:
        self.fig.savefig(path, dpi=150, bbox_inches="tight")
```

**Files:** All three module files  
**Effort:** ~1 hour

---

#### 1.4 Keyboard Shortcut — Ctrl+R to Reset
Bind `<Control-r>` to `_reset()` in all module windows. Document in a footer label.

**Effort:** 30 minutes

---

#### 1.5 Fix Phase Label in Module 03
Change `"Phase Δφ"` → `"Phase Δφ  (phasor only)"` and add a tooltip clarifying it doesn't affect the V vs r curve or heat-map.

**Files:** `visibility_vs_intensity.py`  
**Effort:** 15 minutes

---

### Phase 2 — Medium UX Improvements

#### 2.1 Beginner / Advanced Mode in Module 02
Add a `[ BEGINNER | ADVANCED ]` toggle button at the top of Module 02's control panel.
- **Beginner:** shows only λ, d, L, γ (4 sliders). Hides Δx, θ, I₁, I₂, anim speed.
- **Advanced:** all 9 sliders visible (current behaviour).

Dramatically reduces cognitive load for first-time users.

**Files:** `fringe_pattern.py`  
**Effort:** ~2 hours

---

#### 2.2 Slider Debounce (~30 ms)
Prevent rendering from firing 30+ times per second during rapid dragging.

```python
def _debounced_update(self, *_):
    if hasattr(self, "_upd_id"):
        self.root.after_cancel(self._upd_id)
    self._upd_id = self.root.after(30, self._update)
```

Replace all `self._update()` calls inside `var.trace_add` callbacks with `self._debounced_update()`.

**Files:** All three module files  
**Effort:** ~1 hour

---

#### 2.3 Module 02 — Expose Envelope Width
Add a `σ envelope` slider (range: 2–20 × β, default 8β) so users can control the Gaussian diffraction envelope width. This makes the single-slit diffraction envelope physically visible and tunable.

**Files:** `fringe_pattern.py`  
**Effort:** ~1 hour

---

#### 2.4 Launcher — Process Status Dots
Track PIDs of launched subprocesses. Poll every 1 s with `process.poll()`. Show a coloured dot on each `ModuleRow`:
- ⚫ Grey — not launched yet
- 🟢 Green — running
- 🔴 Red — exited / crashed

**Files:** `launcher.py`  
**Effort:** ~2 hours

---

#### 2.5 Live Formula Substitution in All Modules
Module 02 already has a live φ formula box. Extend this pattern to M01 and M03, showing full numerical substitution of the key visibility formula on every slider move.

Example for Module 01:
```
V = 2·√(I₁·I₂) / (I₁ + I₂)
  = 2·√(1.50 × 0.80) / (1.50 + 0.80)
  = 2·1.095 / 2.300
  = 0.9522
```

**Files:** `two_beams_variation.py`, `visibility_vs_intensity.py`  
**Effort:** ~2 hours

---

### Phase 3 — New Features

#### 3.1 Module 04 — Coherence Length & Temporal Coherence Simulator (NEW)

**File:** `coherence_length.py`

Explores **temporal coherence** — how fringe visibility degrades as the optical path difference approaches and exceeds the coherence length. This is the one key concept not covered by the existing three modules.

**Physics:**
```
L_c   = λ² / Δλ                          coherence length from linewidth
V(Δx) = exp(−(Δx / L_c)²)               Gaussian coherence envelope
I(y)  = [I₁+I₂+2√(I₁I₂)·V(Δx)·cos(2π·Δx/λ + k·y)]
```

**Parameters:** λ (nm), Δλ linewidth (nm), I₁, I₂, current Δx (path difference)

**Plots (3 axes):**
- **Top:** V vs Δx curve with coherence length `L_c` marked as a vertical line
- **Bottom-left:** Actual fringe pattern at current Δx showing real-time visibility wash-out
- **Bottom-right:** Coherence function `|γ(τ)|` vs time delay τ = Δx/c

**Add to launcher:** `MODULES` list entry #04 with amber accent `#ffaa00`.

**Effort:** ~6–8 hours

---

#### 3.2 Module 04 Alternative — Multi-Slit / Diffraction Grating (bonus)

If Module 04 scope is preferred to stay spatial rather than temporal, a **multi-slit grating** simulator (N slits, adjustable slit width and separation) would be a natural extension. Produces characteristic sinc × sinc² patterns.

**Effort:** ~5 hours

---

#### 3.3 Anim FPS Display in Module 02
Show actual achieved FPS next to the animation speed slider, computed from `time.perf_counter()` in `_step_anim`.

```python
import time
def _step_anim(self):
    t0 = time.perf_counter()
    ...
    elapsed = time.perf_counter() - t0
    self.fps_lbl.config(text=f"{1/max(elapsed,0.001):.0f} fps")
```

**Files:** `fringe_pattern.py`  
**Effort:** 30 minutes

---

### Phase 4 — Polish & Performance

#### 4.1 Adaptive Grid Resolution
In Module 02, use a coarser grid during animation and full resolution when paused.

```python
GRID_FULL = (500, 3000)   # static / slider release
GRID_ANIM = (200, 800)    # during animation loop
```

**Files:** `fringe_pattern.py`  
**Effort:** ~1 hour

---

#### 4.2 Shared `theme.py`
Extract colour constants and the `_slider` helper into a shared `theme.py`. All modules import from it. Makes re-theming trivial and eliminates duplication.

> [!WARNING]
> This breaks the "each file is standalone" design principle. Discussed in Open Questions.

**Effort:** ~2 hours (refactor, no new features)

---

#### 4.3 High-DPI Awareness (Windows)
Add at the top of every file:

```python
import sys, ctypes
if sys.platform == "win32":
    try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except: pass
```

Prevents blurry text on 4K / high-DPI displays.

**Effort:** 10 minutes per file

---

#### 4.4 Light Theme Toggle
A `☀ / ☾` button in the Launcher and each module switches the full colour dict between the dark theme and a light variant (white/light-grey background, dark text). Useful for classroom projector use.

**Effort:** ~3 hours

---

#### 4.5 Matplotlib Toolbar (Optional)
Expose `NavigationToolbar2Tk` at the bottom of each module's plot area — gives pan, zoom, home, and a built-in save button. Can be hidden behind a `☰` toggle to avoid conflicting with the formula strip in Module 02.

**Effort:** ~1 hour

---

## Part 4 — Prioritised Execution Roadmap

| Priority | Feature | Est. Effort | Impact |
|---|---|---|---|
| 🔴 **P0** | Tooltip system (U1) | 3 h | High — reduces confusion immediately |
| 🔴 **P0** | Preset buttons (U2) | 2 h | High — improves discoverability |
| 🔴 **P0** | Export plot button (U3) | 1 h | High — essential for student/lab use |
| 🟠 **P1** | Fix Phase Δφ label in M03 (U4) | 0.25 h | Medium — removes confusion |
| 🟠 **P1** | Ctrl+R keyboard reset (U6) | 0.5 h | Medium |
| 🟠 **P1** | Slider debounce (P3) | 1 h | Medium — smooths M02 animation |
| 🟠 **P1** | Beginner/Advanced mode in M02 (U7) | 2 h | Medium — UX clarity |
| 🟡 **P2** | Launcher process status dots (U5) | 2 h | Medium |
| 🟡 **P2** | Live formula substitution in M01/M03 | 2 h | Medium — educational value |
| 🟡 **P2** | Module 04 — Coherence Length sim | 8 h | High new value-add |
| 🟡 **P2** | Expose envelope σ slider in M02 | 1 h | Medium |
| 🟢 **P3** | Shared `theme.py` refactor (C1/C2) | 2 h | Low now, high long-term |
| 🟢 **P3** | High-DPI awareness (U9) | 0.5 h | Low effort, high polish |
| 🟢 **P3** | Adaptive grid resolution in M02 (P1) | 1 h | Medium performance gain |
| 🟢 **P3** | Anim FPS display in M02 | 0.5 h | Nice-to-have |
| 🔵 **P4** | Light theme toggle (U10) | 3 h | Low priority |
| 🔵 **P4** | Matplotlib toolbar toggle (U8) | 1 h | Low |

**Total estimated effort for P0 + P1:** ~10 hours  
**Total for full roadmap:** ~31 hours

---

## Part 5 — Open Questions / Decisions Needed

> [!IMPORTANT]
> **Q1 — Module 04 topic:** Should it be a **Coherence Length** simulator (temporal coherence, V vs Δx) or a **Multi-Slit / Diffraction Grating** simulator (N slits, sinc envelope)? Both are natural extensions; the coherence one fills a physics gap the others leave, the multi-slit one is more visually dramatic.

> [!IMPORTANT]
> **Q2 — Shared `theme.py`:** Creating a shared module breaks the "each file is independently runnable" design principle. Is that trade-off acceptable? Alternative: keep constants duplicated but add a comment block marking them as "sync with theme.py".

> [!NOTE]
> **Q3 — Light theme:** The dark aesthetic is central to the visual identity. A light theme is useful for classroom projectors but adds implementation complexity. Worth doing?

> [!NOTE]
> **Q4 — Matplotlib toolbar vs formula strip:** Adding the built-in Matplotlib toolbar conflicts with Module 02's pinned formula strip at the bottom. A layout decision is needed before implementing.

---

*Fringe Visibility Analyzer — Analysis & Plan by Antigravity, 2026-05-02*
