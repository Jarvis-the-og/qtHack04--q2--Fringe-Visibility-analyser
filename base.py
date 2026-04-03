import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- MAIN APP ----------------
class FringeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fringe Visibility Analyzer")

        # Mode
        self.mode = tk.StringVar(value="two_beam")

        # Sliders
        self.I1 = tk.DoubleVar(value=1.0)
        self.I2 = tk.DoubleVar(value=1.0)

        self.setup_ui()
        self.plot_graph()

    def setup_ui(self):
        # Mode Buttons
        frame_top = tk.Frame(self.root)
        frame_top.pack()

        ttk.Button(frame_top, text="Two Beam",
                   command=lambda: self.change_mode("two_beam")).pack(side=tk.LEFT)

        ttk.Button(frame_top, text="Fringe Pattern",
                   command=lambda: self.change_mode("fringe")).pack(side=tk.LEFT)

        ttk.Button(frame_top, text="Visibility",
                   command=lambda: self.change_mode("visibility")).pack(side=tk.LEFT)

        # Sliders
        frame_controls = tk.Frame(self.root)
        frame_controls.pack()

        tk.Label(frame_controls, text="I1").pack()
        tk.Scale(frame_controls, from_=0.1, to=5,
                 resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.I1, command=lambda x: self.plot_graph()).pack()

        tk.Label(frame_controls, text="I2").pack()
        tk.Scale(frame_controls, from_=0.1, to=5,
                 resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.I2, command=lambda x: self.plot_graph()).pack()

        # Matplotlib Figure
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()

        # Output
        self.output_label = tk.Label(self.root, text="")
        self.output_label.pack()

    def change_mode(self, mode):
        self.mode.set(mode)
        self.plot_graph()

    def plot_graph(self):
        I1 = self.I1.get()
        I2 = self.I2.get()

        self.ax.clear()

        if self.mode.get() == "two_beam":
            phi = np.linspace(0, 2*np.pi, 500)
            I = I1 + I2 + 2*np.sqrt(I1*I2)*np.cos(phi)

            self.ax.plot(phi, I)
            self.ax.set_title("Two Beam Interference")

        elif self.mode.get() == "fringe":
            x = np.linspace(0, 10, 1000)
            I = I1 + I2 + 2*np.sqrt(I1*I2)*np.cos(2*np.pi*x)

            self.ax.plot(x, I)
            self.ax.set_title("Fringe Pattern")

        elif self.mode.get() == "visibility":
            r = np.linspace(0.01, 5, 500)
            V = (2*np.sqrt(r)) / (1 + r)

            self.ax.plot(r, V)
            self.ax.set_title("Visibility vs Intensity Ratio")
            self.ax.set_xlabel("I2 / I1")
            self.ax.set_ylabel("Visibility")

        # Compute visibility
        V_current = (2*np.sqrt(I1*I2)) / (I1 + I2)
        self.output_label.config(text=f"Visibility = {V_current:.3f}")

        self.canvas.draw()


# ---------------- RUN ----------------
root = tk.Tk()
app = FringeApp(root)
root.mainloop()