# Fringe Visibility Analyzer

An interactive physics simulation suite for exploring how unequal beam intensities affect interference fringe contrast and visibility — built with Python, Tkinter, and Matplotlib.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9 or higher |
| matplotlib | ≥ 3.5 |
| numpy | ≥ 1.21 |

Install dependencies:

```bash
pip install matplotlib numpy
```

---

## Project Structure

```
qTHack04/
├── launcher.py                 ← Main menu — start here
├── two_beams_variation.py      ← Simulation 1
├── fringe_pattern.py           ← Simulation 2
├── visibility_vs_intensity.py  ← Simulation 3
└── README.md
```

All four files must be in the **same folder**.

---

## How to Run

```bash
python launcher.py
```

The launcher opens a card-based menu. Click **LAUNCH** on any card to open that simulation in its own window. All three can run simultaneously.

You can also run each simulation directly:

```bash
python two_beams_variation.py
python fringe_pattern.py
python visibility_vs_intensity.py
```

---

## The Three Simulations

### 1 · Two Beams Variation

Demonstrates how two interfering beams with adjustable properties combine into a resultant intensity pattern.

**Sliders:**

| Slider | Symbol | Range | Effect |
|---|---|---|---|
| Beam 1 Intensity | I₁ | 0.01 – 2.0 W | Amplitude of beam 1 |
| Beam 2 Intensity | I₂ | 0.01 – 2.0 W | Amplitude of beam 2 |
| Phase Offset | Δφ | 0 – 360° | Shifts beam 2 relative to beam 1 |
| Spatial Frequency | k | 1.0 – 12.0 | Controls fringe density |

**Panels displayed:**
- Top — Combined intensity pattern I(x) with Imax / Imin markers
- Bottom-left — Beam 1 profile
- Bottom-right — Beam 2 profile

**Live metrics:** Visibility V, Imax, Imin, intensity ratio I₁/I₂

**Core equation:**

```
I(x) = I₁ + I₂ + 2√(I₁·I₂) · cos(kx + Δφ)
V    = 2√(I₁·I₂) / (I₁ + I₂)
```

---

### 2 · Fringe Pattern Simulator

Full Young's double-slit geometry rendered as a live 2-D fringe image on a simulated screen.

**Sliders:**

| Slider | Symbol | Range | Effect |
|---|---|---|---|
| Wavelength | λ | 380 – 780 nm | Colour and fringe scale |
| Slit Separation | d | 0.05 – 3.0 mm | Fringe spacing (inversely) |
| Screen Distance | L | 0.1 – 3.0 m | Fringe spacing (directly) |
| Beam 1 Intensity | I₁ | 0.01 – 2.0 W | Bright fringe peak |
| Beam 2 Intensity | I₂ | 0.01 – 2.0 W | Bright fringe peak |
| Coherence Factor | γ | 0.0 – 1.0 | Degrades visibility smoothly |
| Tilt Angle | θ | −30 – +30° | Shifts the entire pattern laterally |

**Panels displayed:**
- Top — 2-D fringe pattern with Gaussian slit-width envelope
- Bottom-left — 1-D intensity cross-section with fringe-width annotation β
- Bottom-right — Visible spectrum bar with current λ highlighted

**Core equations:**

```
β  = λL / d                         (fringe width)
V  = γ · 2√(I₁·I₂) / (I₁ + I₂)    (effective visibility)
I(y) = (I₁+I₂)[1 + V·cos(2πdy/λL)]
```

---

### 3 · Visibility vs Intensity Ratio

Plots the analytic visibility curve against the intensity ratio r = I₁/I₂. A live marker tracks your current point on the curve as you move the sliders.

**Sliders:**

| Slider | Symbol | Range | Effect |
|---|---|---|---|
| Beam 1 Intensity | I₁ | 0.01 – 5.0 W | Moves marker on curve |
| Beam 2 Intensity | I₂ | 0.01 – 5.0 W | Moves marker on curve |
| Phase Offset | Δφ | 0 – 360° | Rotates phasor diagram |
| X-axis max | — | 2 – 50 | Zoom level of ratio axis |

**Panels displayed:**
- Top — V vs r curve with quality-zone shading and live marker (hot-pink)
- Bottom-left — Phasor diagram (polar): E₁, E₂, and resultant amplitude
- Bottom-right — 2-D visibility heat-map over all (I₁, I₂) combinations; diagonal = V = 1

**Fringe quality bands:**

| Band | Visibility Range | Colour |
|---|---|---|
| Excellent | V ≥ 0.90 | Lime |
| Good | 0.70 – 0.90 | Cyan |
| Moderate | 0.40 – 0.70 | Orange |
| Poor | < 0.40 | Red-pink |

**Core identity:**

```
r  = I₁ / I₂
V  = 2√r / (1 + r)      maximum at r = 1  →  V = 1
                          V → 0  as r → ∞
```

---

## Key Physics Reference

### Michelson Visibility (Fringe Contrast)

```
V = (Imax − Imin) / (Imax + Imin)
```

- V = 1 → perfect fringes (equal intensities, full coherence)
- V = 0 → no fringes (completely incoherent or one beam blocked)

### Imax and Imin for Two-Beam Interference

```
Imax = (√I₁ + √I₂)²
Imin = (√I₁ − √I₂)²
```

### Effect of Coherence

Partial coherence multiplies the intrinsic visibility by γ ∈ [0, 1]:

```
V_eff = γ · V_intrinsic
```

---

## Controls Quick Reference

| Action | How |
|---|---|
| Adjust a parameter | Drag the slider |
| See current value | Read the label to the right of each slider |
| Reset to defaults | Click the **⟳ RESET** button |
| Open a simulation | Click **LAUNCH** in the launcher, or run the `.py` directly |
| Close a simulation | Close its window; other windows are unaffected |

---

## Troubleshooting

**`_tkinter.TclError: unknown option "-letter_spacing"`**  
Make sure you are using the corrected `launcher.py` — older versions had an unsupported Tkinter kwarg. Replace with the latest file.

**Blank / white plot area**  
Ensure `matplotlib` is installed and TkAgg backend is available: `pip install matplotlib`.

**Simulation window does not open from launcher**  
All `.py` files must be in the same directory. Check with:
```bash
ls   # (macOS/Linux)
dir  # (Windows)
```

**Slow rendering on high-DPI screens**  
Resize the window slightly smaller — matplotlib redraws at native resolution.

---

## Built With

- **Python 3** — core language
- **Tkinter** — GUI framework (bundled with Python)
- **Matplotlib** (TkAgg backend) — all plots and animations
- **NumPy** — physics calculations

---

*Fringe Visibility Analyzer — qTHack04*