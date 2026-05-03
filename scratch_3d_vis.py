import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Barrier
d = 2
wall_w = 10
wall_h = 4
slit_w = 0.5
Z_slit = 0

polys = [
    [[-wall_w/2, -wall_h/2, Z_slit], [-d/2-slit_w/2, -wall_h/2, Z_slit], [-d/2-slit_w/2, wall_h/2, Z_slit], [-wall_w/2, wall_h/2, Z_slit]],
    [[-d/2+slit_w/2, -wall_h/2, Z_slit], [d/2-slit_w/2, -wall_h/2, Z_slit], [d/2-slit_w/2, wall_h/2, Z_slit], [-d/2+slit_w/2, wall_h/2, Z_slit]],
    [[d/2+slit_w/2, -wall_h/2, Z_slit], [wall_w/2, -wall_h/2, Z_slit], [wall_w/2, wall_h/2, Z_slit], [d/2+slit_w/2, wall_h/2, Z_slit]]
]
ax.add_collection3d(Poly3DCollection(polys, facecolors='#333333', edgecolors='k', alpha=0.9))

# Concentric semi-circles for waves
radii = np.linspace(0.5, 5, 8)
theta = np.linspace(0, np.pi, 50)
for r in radii:
    # Slit 1
    x1 = -d/2 + r * np.cos(theta)
    y1 = np.zeros_like(theta)
    z1 = Z_slit + r * np.sin(theta)
    ax.plot(x1, y1, z1, color='red', alpha=1 - r/6, lw=2)
    
    # Slit 2
    x2 = d/2 + r * np.cos(theta)
    y2 = np.zeros_like(theta)
    z2 = Z_slit + r * np.sin(theta)
    ax.plot(x2, y2, z2, color='red', alpha=1 - r/6, lw=2)

# Wavy incoming
X_in = np.linspace(-wall_w/2, wall_w/2, 30)
Z_in = np.linspace(-6, Z_slit, 30)
X_in, Z_in = np.meshgrid(X_in, Z_in)
# Wave equation: cos(k*Z)
Y_in = 0.5 * np.cos(3 * Z_in)
# We can use plot_surface
ax.plot_surface(X_in, Y_in, Z_in, color='blue', alpha=0.3, shade=False)

ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
ax.set_zlim(-6, 6)
plt.show()
