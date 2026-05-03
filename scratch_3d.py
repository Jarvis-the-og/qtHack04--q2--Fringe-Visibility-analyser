import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

d = 0.5  # mm
L = 1.0  # m
# Let's scale Z axis to be proportional, but since L is in meters and d in mm, it will look squashed.
# Let's just use normalized units for visual appeal.
Z_slit = 0
Z_screen = 10 # visual scale

# Slit plane
# Let's draw a wall with two slits
wall_width = 4
wall_height = 4

# draw wall as 3 polygons
# left part, middle part, right part
gap = 0.2
slit_w = 0.1

polys = [
    [[-wall_width/2, -wall_height/2, Z_slit], [-d/2-slit_w/2, -wall_height/2, Z_slit], [-d/2-slit_w/2, wall_height/2, Z_slit], [-wall_width/2, wall_height/2, Z_slit]], # left
    [[-d/2+slit_w/2, -wall_height/2, Z_slit], [d/2-slit_w/2, -wall_height/2, Z_slit], [d/2-slit_w/2, wall_height/2, Z_slit], [-d/2+slit_w/2, wall_height/2, Z_slit]], # middle
    [[d/2+slit_w/2, -wall_height/2, Z_slit], [wall_width/2, -wall_height/2, Z_slit], [wall_width/2, wall_height/2, Z_slit], [d/2+slit_w/2, wall_height/2, Z_slit]], # right
]

ax.add_collection3d(Poly3DCollection(polys, facecolors='cyan', linewidths=1, edgecolors='b', alpha=0.3))

# Screen
screen = [[[-wall_width/2, -wall_height/2, Z_screen], [wall_width/2, -wall_height/2, Z_screen], [wall_width/2, wall_height/2, Z_screen], [-wall_width/2, wall_height/2, Z_screen]]]
ax.add_collection3d(Poly3DCollection(screen, facecolors='gray', linewidths=1, edgecolors='k', alpha=0.5))

# Light beams
ax.plot([-d/2, 0], [0, 0], [Z_slit, Z_screen], color='red')
ax.plot([d/2, 0], [0, 0], [Z_slit, Z_screen], color='red')

ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_zlim(-1, 11)

plt.show()
