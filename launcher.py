"""
Fringe Visibility Analyzer  –  Main Launcher
Launches any of the three simulation windows.
"""

import tkinter as tk
from tkinter import messagebox
import subprocess, sys, os

BG      = "#0b0d17"
PANEL   = "#111420"
ACCENT  = "#00d4ff"
ACCENT2 = "#ff6b35"
GOOD    = "#7fff7f"
TEXT    = "#dde4f0"
SUBTEXT = "#6b728c"
HI      = "#1c2030"

CARDS = [
    {
        "id":    "two_beams",
        "title": "TWO BEAMS\nVARIATION",
        "desc":  ("Adjust individual beam intensities I₁ and I₂,\n"
                  "phase offset Δφ, and spatial frequency k.\n"
                  "Watch beam profiles and the combined pattern\n"
                  "update in real time."),
        "file":  "two_beams_variation.py",
        "color": "#00d4ff",
        "icon":  "〰",
    },
    {
        "id":    "fringe_pattern",
        "title": "FRINGE PATTERN\nSIMULATOR",
        "desc":  ("Full Young's double-slit geometry. Control\n"
                  "wavelength λ, slit separation d, screen\n"
                  "distance L, coherence γ, and tilt angle θ.\n"
                  "Renders a live 2-D fringe pattern."),
        "file":  "fringe_pattern.py",
        "color": "#7df9ff",
        "icon":  "≋",
    },
    {
        "id":    "visibility_ratio",
        "title": "VISIBILITY vs\nINTENSITY RATIO",
        "desc":  ("Plots the analytic curve V = 2√r/(1+r).\n"
                  "Live marker tracks current I₁/I₂ ratio.\n"
                  "Includes phasor diagram and a 2-D\n"
                  "visibility heat-map over (I₁, I₂) space."),
        "file":  "visibility_vs_intensity.py",
        "color": "#c8ff5c",
        "icon":  "◈",
    },
]


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fringe Visibility Analyzer  ·  Launcher")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG, pady=24)
        hdr.pack(fill="x", padx=40)
        tk.Label(hdr, text="FRINGE VISIBILITY",
                 font=("Courier", 28, "bold"), fg=ACCENT, bg=BG).pack()
        tk.Label(hdr, text="A  N  A  L  Y  Z  E  R",
                 font=("Courier", 13, "bold"), fg=SUBTEXT, bg=BG).pack()
        tk.Frame(self, bg=HI, height=1).pack(fill="x", padx=40)

        # ── Subtitle ─────────────────────────────────────────────────────────
        tk.Label(self,
                 text=("Explore how unequal beam intensities affect fringe contrast\n"
                       "through three interactive physics simulations."),
                 font=("Courier", 10), fg=SUBTEXT, bg=BG,
                 justify="center").pack(pady=16)

        # ── Cards ────────────────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=BG)
        cards_frame.pack(padx=30, pady=(0, 20))

        for card in CARDS:
            self._make_card(cards_frame, card)

        # ── Footer ──────────────────────────────────────────────────────────
        tk.Frame(self, bg=HI, height=1).pack(fill="x", padx=40)
        tk.Label(self,
                 text="Select a simulation to open it in a new window.",
                 font=("Courier", 8), fg=SUBTEXT, bg=BG).pack(pady=10)

    def _make_card(self, parent, card):
        col = card["color"]
        frm = tk.Frame(parent, bg=PANEL, relief="flat", pady=18, padx=22)
        frm.pack(fill="x", pady=8)

        # Left accent bar
        bar = tk.Frame(frm, bg=col, width=4)
        bar.pack(side="left", fill="y", padx=(0, 16))

        body = tk.Frame(frm, bg=PANEL)
        body.pack(side="left", fill="both", expand=True)

        icon_lbl = tk.Label(body, text=card["icon"],
                            font=("Courier", 28), fg=col, bg=PANEL)
        icon_lbl.pack(side="left", padx=(0, 16))

        info = tk.Frame(body, bg=PANEL)
        info.pack(side="left", fill="both", expand=True)

        tk.Label(info, text=card["title"],
                 font=("Courier", 13, "bold"), fg=col,
                 bg=PANEL, justify="left").pack(anchor="w")
        tk.Label(info, text=card["desc"],
                 font=("Courier", 9), fg=SUBTEXT,
                 bg=PANEL, justify="left").pack(anchor="w", pady=(4, 0))

        btn = tk.Button(frm, text="LAUNCH  ▶",
                        font=("Courier", 9, "bold"),
                        fg=BG, bg=col, relief="flat", bd=0,
                        padx=14, pady=7, cursor="hand2",
                        command=lambda f=card["file"]: self._launch(f))
        btn.pack(side="right", padx=(16, 0))

        # Hover effect
        btn.bind("<Enter>", lambda e, b=btn, c=col: b.config(bg="white", fg=c))
        btn.bind("<Leave>", lambda e, b=btn, c=col: b.config(bg=c, fg=BG))

    def _launch(self, filename):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, filename)
        if not os.path.exists(path):
            messagebox.showerror("File not found",
                                 f"Could not find:\n{path}")
            return
        subprocess.Popen([sys.executable, path])


def main():
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
