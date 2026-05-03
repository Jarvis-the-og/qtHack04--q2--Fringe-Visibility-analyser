# Fringe Visibility Analyzer

> An interactive desktop suite for exploring how beam intensity, coherence, and geometry govern fringe contrast in two-beam optical interference experiments.

---

## Table of Contents

1. [Overview](#overview)
2. [Physics Background](#physics-background)
   - [What is Fringe Visibility?](#what-is-fringe-visibility)
   - [Two-Beam Interference](#two-beam-interference)
   - [Effect of Unequal Intensities](#effect-of-unequal-intensities)
   - [Coherence and Spatial Geometry](#coherence-and-spatial-geometry)
3. [Project Structure](#project-structure)
4. [Installation & Requirements](#installation--requirements)
5. [Running the Application](#running-the-application)
6. [Module Reference](#module-reference)
   - [Module 01 — Fringe Pattern Simulator](#module-01--fringe-pattern-simulator)
   - [Module 02 — Visibility vs Intensity Ratio](#module-02--visibility-vs-intensity-ratio)
7. [UI Architecture](#ui-architecture)
   - [Launcher Window](#launcher-window)
   - [Scrolling & Responsiveness](#scrolling--responsiveness)
   - [Colour System & Design Tokens](#colour-system--design-tokens)
8. [Control Reference](#control-reference)
   - [Module 01 Controls](#module-01-controls)
   - [Module 02 Controls](#module-02-controls)
9. [Live Metrics Explained](#live-metrics-explained)
10. [Animation System (Module 01)](#animation-system-module-01)
11. [Key Formulas Quick Reference](#key-formulas-quick-reference)
12. [Known Fixes & Patch Notes](#known-fixes--patch-notes)
13. [Keyboard Shortcuts](#keyboard-shortcuts)
14. [Extending the Suite](#extending-the-suite)
15. [Troubleshooting](#troubleshooting)

---

## Overview

The **Fringe Visibility Analyzer** is a multi-window Python/Tkinter desktop application backed by Matplotlib for real-time scientific visualization. It is aimed at students, educators, and researchers who want an intuitive, hands-on way to understand the physics of optical interference — specifically how the *visibility* (contrast) of interference fringes responds to changes in beam intensity, path difference, coherence, and experimental geometry.

The suite launches from a central **Launcher** window that presents background theory and links to two independent simulation modules. Each module opens in its own window and can run simultaneously; no module depends on another at runtime.

All plots update in real time as the user drags sliders — there are no "Apply" buttons. The suite runs entirely offline; no network connection is required.

---

## Physics Background

### What is Fringe Visibility?

When two coherent light beams overlap they form an **interference pattern**: alternating bright and dark bands called *fringes*. The sharpness of this pattern is quantified by the **Michelson fringe visibility** (also called fringe contrast):

```
V = (I_max − I_min) / (I_max + I_min)
```

where `I_max` is the intensity at a bright fringe peak and `I_min` is the intensity at a dark fringe trough.

The visibility ranges from 0 to 1:

| V | Interpretation |
|---|----------------|
| 1.000 | Perfect contrast — dark fringes are completely black |
| ≥ 0.90 | Excellent — fringes are easily resolved |
| 0.70 – 0.90 | Good — fringes clearly visible with minor wash-out |
| 0.40 – 0.70 | Moderate — fringes detectable but washed out |
| < 0.40 | Poor — barely distinguishable from uniform illumination |
| 0.000 | No fringes — uniform illumination |

### Two-Beam Interference

For two monochromatic plane waves with intensities `I₁` and `I₂` and a relative phase difference `Δφ`, the combined intensity at a point on the screen is:

```
I(x) = I₁ + I₂ + 2 · √(I₁ · I₂) · cos(k·x + Δφ)
```

where:
- `k` is the spatial frequency of the fringe pattern (rad/m)
- `x` is position along the screen
- `Δφ` is the relative phase offset between the two beams (radians)

The first two terms give a uniform background; the cosine term produces the oscillating fringes. The amplitude of that oscillation, `2√(I₁·I₂)`, is maximized when `I₁ = I₂`.

### Effect of Unequal Intensities

For two perfectly coherent beams the maximum achievable visibility is determined solely by the intensity balance:

```
V = 2·√(I₁ · I₂) / (I₁ + I₂)
```

This can equivalently be written in terms of the ratio `r = I₁/I₂`:

```
V = 2·√r / (1 + r)
```

Key observations:
- **r = 1** (equal intensities): `V = 1` — perfect contrast.
- **r = 4** (4:1 ratio): `V = 0.800` — already noticeably degraded.
- **r = 9** (9:1 ratio): `V = 0.600` — moderate contrast.
- **r → ∞**: `V → 0` — one beam dominates and fringes disappear.

The formula reflects the geometric-mean–to–arithmetic-mean ratio of the electric-field amplitudes. Any deviation from equal intensity *strictly reduces* visibility.

### Coherence and Spatial Geometry

The intensity formula above assumes perfect temporal and spatial coherence. In practice, a **coherence factor** `γ ∈ [0, 1]` multiplies the interference term:

```
I(y) = I₁ + I₂ + 2·√(I₁·I₂) · γ · cos(k·y + φ)
```

The effective visibility therefore becomes:

```
V_eff = γ · V_intensity = γ · [2·√(I₁·I₂) / (I₁ + I₂)]
```

In Young's double-slit geometry:
- The **spatial frequency** is `k = 2πd / (λL)`, where `d` is slit separation, `λ` wavelength, and `L` screen distance.
- The **fringe width** (period) is `β = λL / d`.
- A **path difference** `Δx` introduces a phase shift `φ = 2πΔx / λ`, which translates the entire pattern laterally by `y₀ = −φ/k = −ΔxL/d`.
- A **tilt angle** `θ` of one beam adds a further shift `y_tilt = −L·tan(θ)`.

---

## Project Structure

```
fringe-visibility-analyzer/
│
├── launcher.py                  # Main entry point — the hub window
├── fringe_pattern.py            # Module 01 — full Young's DSE simulator
├── visibility_vs_intensity.py   # Module 02 — analytic curve + heat-map
│
└── README.md                    # This file
```

All three files are self-contained. The launcher discovers module files relative to its own location using `os.path.dirname(os.path.abspath(__file__))`, so the working directory does not need to match the source directory.

---

## Installation & Requirements

### Python version

Python **3.9 or later** is recommended. The code uses standard library features only (no walrus operators, no 3.10+ match statements), so 3.8 should also work.

### Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `tkinter` | GUI framework | Bundled with CPython (Linux: `python3-tk`) |
| `matplotlib` | Plotting backend | `pip install matplotlib` |
| `numpy` | Numerical arrays | `pip install numpy` |

No other third-party packages are required.

### Platform notes

The suite is developed and tested on **Linux (X11)** and **Windows 10/11**. On macOS, the TkAgg Matplotlib backend may require XQuartz or an additional backend configuration; use `matplotlib.use("TkAgg")` as already set in each module.

```bash
# Debian/Ubuntu — ensure Tkinter is present
sudo apt install python3-tk

# All platforms — install Python dependencies
pip install matplotlib numpy
```

---

## Running the Application

### Via the Launcher (recommended)

```bash
python launcher.py
```

The Launcher window opens maximized. Click **Launch ▶** on any module card to open that simulation in a separate window. Multiple modules can run simultaneously.

### Running a module directly

Each simulation file is independently executable:

```bash
python fringe_pattern.py
python visibility_vs_intensity.py
```

---

## Module Reference

### Module 01 — Fringe Pattern Simulator

**File:** `fringe_pattern.py`  
**Window size:** 1380 × 880 px (resizable)

The most comprehensive module. It implements the full Young's double-slit geometry and renders three panels plus a bottom physics-reference strip:

| Plot | Description |
|------|-------------|
| **Top (full width)** | 2-D fringe pattern image rendered with a custom blue-white-blue colormap (`FRINGE_CMAP`). A vertical gold dashed line marks the central maximum, which shifts live with `Δx` and `θ`. |
| **Bottom-left** | 1-D intensity cross-section `I(y)` with a double-headed arrow annotating the fringe width `β`, and a vertical gold marker at the central maximum. |
| **Bottom-right** | Visible spectrum bar (380–780 nm) with a white cursor at the selected wavelength `λ`. |

A **formula strip** across the bottom of the window displays all six key physics relationships simultaneously, providing a constant reference without cluttering the control panel.

**Physics implemented:**

```
k  = 2πd / (λL)          — spatial frequency
φ  = 2π·Δx / λ           — phase from path difference
β  = λL / d               — fringe width
y₀ = −φ/k                 — central-maximum shift
I  = I₁+I₂+2√(I₁I₂)·γ·cos(k·(y − L·tan θ) + φ)
V  = γ · 2√(I₁I₂) / (I₁+I₂)
```

A Gaussian envelope `exp(−y²/2σ²)` with `σ = 8β` simulates the finite-slit diffraction envelope.

**Animation feature:** The `Δx` slider can be animated automatically (see [Animation System](#animation-system-module-01)), sweeping the path difference back and forth to show moving fringes in real time.

---

### Module 02 — Visibility vs Intensity Ratio

**File:** `visibility_vs_intensity.py`  
**Window size:** 1440 × 860 px (resizable)

This module focuses on the *analytic* relationship `V = 2√r/(1+r)` and complements it with two geometric visualizations:

| Plot | Description |
|------|-------------|
| **Top (full width)** | The `V vs r` curve over a user-configurable x-range. Quality zones are colour-coded (Excellent / Good / Moderate / Poor). A live hot-pink scatter marker with crosshairs tracks the current `(r, V)` point. A text annotation displays the exact values at the marker. |
| **Bottom-left** | **Phasor diagram** on polar axes. Electric-field amplitudes `E₁ = √I₁` and `E₂ = √I₂` are drawn as radial lines at angles 0 and `Δφ` respectively. The resultant `|E|` is drawn as a dashed line. Dots mark each tip; labels are placed just beyond the tip radius. |
| **Bottom-right** | **2-D visibility heat-map** over `(I₁, I₂)` space (0.01–5 W on each axis). Rendered with the `plasma` colormap. A white dashed diagonal marks `I₁ = I₂` (V = 1 locus). A live marker shows the current operating point. |

A **fringe quality badge** in the control panel updates its text and colour dynamically (EXCELLENT / GOOD / MODERATE / POOR) as the user moves sliders.

---

## UI Architecture

### Launcher Window

The Launcher is built as a scrollable single-page layout using a `tk.Canvas` with an embedded `tk.Frame` (the "page"). Content is divided into:

- **Header** — title and subtitle
- **Background section** — two `TheoryBlock` widgets, each with an accent bar, heading, and body text
- **Simulation Modules section** — three `ModuleRow` widgets, one per simulation
- **Footer** — usage hint and version string

Section headings are rendered by the `SectionHeading` compound widget: a small all-caps label followed by a 1-px horizontal rule.

### Scrolling & Responsiveness

Scrolling is handled by a `ttk.Scrollbar` wired to the canvas's `yview`. Mouse-wheel support covers all three common event patterns:

| Event | Platform |
|-------|---------|
| `<MouseWheel>` with `e.delta // 120` | Windows / macOS |
| `<Button-4>` | Linux scroll-up |
| `<Button-5>` | Linux scroll-down |

On window resize (`<Configure>` on the root window), the content column is clamped to `CONTENT_MAX_W = 980 px` and centred horizontally. `wraplength` values on all text-heavy widgets (`TheoryBlock`, `ModuleRow` description labels) are recomputed dynamically via `reflow(available_width)` methods — so text never overflows or leaves large dead space.

### Colour System & Design Tokens

All colours are defined once in a `COLOR` dict (Launcher) or equivalent module-level constants. The palette is a dark-mode scheme built around a near-black background with cyan/lime/orange accents:

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#0b0d17` | Window background |
| `surface` | `#111420` | Card / panel background |
| `border` | `#1e2236` | Dividers, subtle edges |
| `accent` | `#00d4ff` | Primary accent (Module 01 cyan) |
| `text` | `#dde4f0` | Primary readable text |
| `subtext` | `#6b728c` | Secondary / muted text |

Each module defines its own accent palette aligned to its physical interpretation (e.g., cyan, lime-green, orange).

Matplotlib `rcParams` are configured globally in each module to inherit the dark theme, including axes face colour, edge colour, tick colour, grid colour, and font family (`monospace`).

---

## Control Reference

### Module 01 Controls

| Slider | Range | Default | Description |
|--------|-------|---------|-------------|
| **Wavelength λ** | 380 – 780 nm | 550 nm | Optical wavelength (visible spectrum) |
| **Slit separation d** | 0.05 – 3.00 mm | 0.50 mm | Distance between the two slits |
| **Screen distance L** | 0.10 – 3.00 m | 1.00 m | Distance from slits to screen |
| **Path difference Δx** | −50 – 50 μm | 0.00 μm | Optical path difference between beams |
| **I₁ (Beam 1)** | 0.01 – 2.00 W | 1.00 | Intensity of Beam 1 |
| **I₂ (Beam 2)** | 0.01 – 2.00 W | 1.00 | Intensity of Beam 2 |
| **Coherence γ** | 0.00 – 1.00 | 1.00 | Temporal/spatial coherence factor |
| **Tilt angle θ** | −30 – 30 ° | 0 ° | Tilt of one beam relative to the other |
| **Anim speed** | 0.01 – 0.30 | 0.08 | Step size per animation frame (μm) |

**Reset** button (top-right of header) restores all sliders and stops any running animation.

A live **φ formula box** in the control panel updates every time `Δx` or `λ` changes, showing the numerical substitution `φ = 2π·Δx/λ` in real time.

---

### Module 02 Controls

| Slider | Range | Default | Description |
|--------|-------|---------|-------------|
| **I₁ (Beam 1)** | 0.01 – 5.00 W | 1.00 | Intensity of Beam 1 |
| **I₂ (Beam 2)** | 0.01 – 5.00 W | 1.00 | Intensity of Beam 2 |
| **Phase Δφ** | 0 – 360 ° | 0 | Phase shift (affects phasor diagram only) |
| **X-axis max r** | 2.0 – 50.0 | 10.0 | Upper limit of ratio axis on the V vs r curve |

**Reset** button restores all four sliders. The **X-axis max r** slider is particularly useful: at `r = 10` the curve's rapid initial drop is well visible; zooming out to `r = 50` shows the asymptotic approach to V = 0.

---

## Live Metrics Explained

All two modules maintain a live metrics panel that updates on every slider move.

### Module 01 Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Visibility V** | `γ · 2√(I₁I₂)/(I₁+I₂)` | Effective fringe contrast |
| **Fringe width β** | `λL/d` | Spacing between bright fringes (mm) |
| **Bright orders ±N** | Fixed display of ±5 | Number of visible bright orders |
| **Path diff Δx** | Slider value | Current path difference (μm) |
| **Phase φ** | `2π·Δx/λ` | Phase from path difference (rad) |
| **Central max shift** | `−φ/k + y_tilt` | Lateral displacement of m=0 fringe (mm) |

### Module 02 Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **I₁/I₂ ratio r** | `I₁/I₂` | Current intensity ratio |
| **Visibility V** | `2√r/(1+r)` | Visibility at current ratio |
| **I_max** | `(√I₁ + √I₂)²` | Peak intensity |
| **I_min** | `(√I₁ − √I₂)²` | Trough intensity |
| **Contrast C** | Equal to V | Michelson contrast (same as V) |

The **Fringe Quality badge** maps V to a qualitative label:

| V range | Label | Colour |
|---------|-------|--------|
| ≥ 0.90 | EXCELLENT | Lime `#c8ff5c` |
| 0.70 – 0.90 | GOOD | Cyan `#5ce0ff` |
| 0.40 – 0.70 | MODERATE | Orange `#ffa45c` |
| < 0.40 | POOR | Pink `#ff5c8a` |

---

## Animation System (Module 01)

Module 01 includes an **Animate Δx** feature that sweeps the path difference slider automatically, producing a live moving-fringe effect.

**How it works:**

The animation is driven by `root.after(40, self._step_anim)` — a 40 ms polling loop (≈ 25 fps). Each tick advances `Δx` by the current **Anim speed** value (in μm). Direction reverses automatically when the slider hits ±50 μm. Because `Δx` is a `tk.DoubleVar` with a `trace_add("write", ...)` callback, the `_update()` rendering method fires automatically — no explicit call needed in the animation loop.

**Controls:**

- Click **▶ ANIMATE Δx** to start. The button turns red and shows **■ STOP ANIMATION**.
- Click again to stop the animation and return the button to its idle state.
- The **Anim speed** slider adjusts the step size per frame (0.01 – 0.30 μm). Small values produce slow, smooth movement; large values produce rapid fringe sweeps.
- **Reset** automatically stops any running animation before restoring defaults.

---

## Key Formulas Quick Reference

```
Two-beam intensity (general):
  I(x) = I₁ + I₂ + 2·√(I₁·I₂)·γ·cos(k·x + Δφ)

Michelson visibility:
  V = (I_max − I_min) / (I_max + I_min)

Peak and trough intensities:
  I_max = (√I₁ + √I₂)²
  I_min = (√I₁ − √I₂)²

Visibility from intensity ratio:
  V = 2·√(I₁·I₂) / (I₁ + I₂)  =  2·√r / (1 + r)   where r = I₁/I₂

Young's double-slit geometry:
  k  = 2πd / (λL)              [spatial frequency, rad/m]
  β  = λL / d                   [fringe width, m]

Phase from path difference:
  φ  = 2π·Δx / λ               [radians]

Central maximum position:
  y₀ = −φ/k  =  −Δx·L / d     [metres]

Effective visibility with coherence:
  V_eff = γ · 2·√(I₁·I₂) / (I₁ + I₂)
```

---

## Known Fixes & Patch Notes

### Module 02 (`visibility_vs_intensity.py`)

**FIX 1 — Phasor label placement:**
Labels (`E₁`, `E₂`, `|E|`) previously used erroneous Cartesian offsets inside polar axes, causing them to appear at wrong positions or off-screen. Labels now use polar coordinate placement — offset by `r_max * 0.20` beyond each arrow tip along its own angle — so they always sit cleanly at their respective arrowheads regardless of slider position.

**FIX 2 — Visibility heatmap clipping:**
The window was too small for the 2×2 GridSpec layout, causing the bottom-right heatmap and its colorbar to be clipped. The window is now enlarged to **1440 × 860 px** and the GridSpec margins are adjusted (`bottom=0.09`, `wspace=0.42`) to give the heatmap axes sufficient room.

**FIX 3 — Colorbar accumulation:**
Each call to `_update()` previously created a new `colorbar` instance without removing the old one, causing colorbars to stack up and overlap. A single colorbar reference is now stored in `self._cbar`. On each redraw the old colorbar is removed via `self._cbar.remove()` before creating a new one using `make_axes_locatable` for precise sizing.

---

## Keyboard Shortcuts

These shortcuts work in the **Launcher** window. Individual module windows are plain Matplotlib/Tkinter canvases and do not have additional keyboard bindings beyond the standard Matplotlib toolbar.

| Key | Action |
|-----|--------|
| **F11** | Toggle full-screen mode |
| **Escape** | Exit full-screen mode |
| **Mouse wheel** | Scroll the launcher page vertically |

---

## Extending the Suite

The project is designed to be modular and easy to extend. To add a new simulation module:

1. Create a new Python file (e.g., `my_new_module.py`) in the same directory. Follow the pattern of the existing modules: a single application class with `__init__`, `_build_ui`, `_compute`, and `_update` methods.

2. Add an entry to the `MODULES` list in `launcher.py`:
   ```python
   {
       "number": "04",
       "title":  "My New Module",
       "desc":   "A short description shown on the launcher card.",
       "file":   "my_new_module.py",
   }
   ```

3. Optionally add a new accent colour to `MODULE_ACCENTS` in `launcher.py`.

The Launcher will automatically render a new module card and wire up the **Launch ▶** button to open the file via `subprocess.Popen`.

---

## Troubleshooting

**The Launcher opens but clicking Launch does nothing.**
Check that the simulation `.py` files are in the same directory as `launcher.py`. The launcher reports a "File not found" error dialog if the file is missing.

**Plots are slow to update or lag behind slider movement.**
This can happen on machines with integrated graphics or slow Python installations. Try reducing the array resolution: change `np.linspace(0, 2*np.pi, 1000)` to `500` in Module 01, or the 2-D grid size from `500` to `300` in Module 02.

**`_tkinter.TclError: no display name and no $DISPLAY environment variable` on Linux.**
You are running in a headless environment. The suite requires a graphical display. Set up X forwarding (`ssh -X`) or use a virtual display (`Xvfb`).

**Colorbar overlaps the heatmap in Module 02.**
This should be resolved by FIX 2 and FIX 3 (see [Patch Notes](#known-fixes--patch-notes)). If it persists, try maximizing the Module 02 window to give Matplotlib more space for the layout engine to work with.

**`ModuleNotFoundError: No module named 'matplotlib'`.**
Install the dependencies: `pip install matplotlib numpy`.

**The animation in Module 01 runs too fast or too slow.**
Adjust the **Anim speed** slider. The `root.after(40, ...)` call targets ~25 fps; actual speed depends on rendering time per frame on your hardware. Reducing the 2-D array resolution (see above) will also speed up the animation.

**Text in theory blocks wraps incorrectly or overflows.**
This is handled by the `reflow()` method, which fires on every `<Configure>` event. If text still looks wrong, try resizing the Launcher window slightly to force a reflow cycle.

---

*Fringe Visibility Analyzer — v1.0*
