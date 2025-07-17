import numpy as np
import matplotlib.pyplot as plt

u_values = np.arange(200, 325, 5)

f_values = np.arange(-320, -455, -5)

U, F = np.meshgrid(u_values, f_values)

Z = np.zeros_like(U, dtype=float)

x = 100 

for i in range(U.shape[0]):
    for j in range(U.shape[1]):
        u = U[i, j]
        f = F[i, j]

        try:
            y = (u * x) / (100 + (10000 / -f))
            lhs = (100 / -f) * y
            hedge_value = lhs / x
            Z[i, j] = hedge_value
        except ZeroDivisionError:
            Z[i, j] = np.nan

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(U, F, Z, cmap='viridis', edgecolor='k')

ax.set_xlabel("Underdog Odds (+)")
ax.set_ylabel("Favorite Odds (-)")
ax.set_zlabel("Hedge Value")
ax.set_title("Hedge Value vs. Underdog and Favorite Odds")

fig.colorbar(surf, shrink=0.5, aspect=10)

plt.savefig("hedge_value_plot.png", dpi=300, bbox_inches='tight')
plt.show()
print("Graph saved as hedge_value_plot.png")

