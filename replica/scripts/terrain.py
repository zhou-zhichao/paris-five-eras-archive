"""Stylised relief for the Paris basin (pure numpy, shared by growth.py and Blender)."""
import numpy as np

# (x, y, sigma, height)  metres, origin Notre-Dame
HILLS = [
    (-500, 3750, 520, 78),      # Montmartre
    (2500, 2500, 800, 58),      # Belleville / Buttes-Chaumont
    (4800, 2600, 1500, 50),     # Romainville / Montreuil plateau
    (-280, -750, 450, 26),      # Sainte-Genevieve
    (-4300, 900, 550, 26),      # Chaillot
    (300, -2500, 450, 22),      # Butte-aux-Cailles
    (-9800, 3200, 750, 100),    # Mont Valerien
    (-9000, -3800, 1700, 85),   # Meudon / Saint-Cloud plateau
    (-6500, -7500, 2200, 70),   # Bievre / Clamart heights
    (-9500, 10500, 1600, 75),   # Cormeilles / Argenteuil
    (7500, 7000, 2200, 45),     # Aulnay plateau
    (9000, -6000, 2500, 55),    # Sucy / Boissy plateau
    (-14000, 2000, 2600, 90),   # Saint-Germain-en-Laye plateau (far west)
    (-2500, -12500, 3000, 70),  # southern plateau
]


def height(x, y):
    """Raw relief height (metres) before water damping."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    z = np.zeros(np.broadcast(x, y).shape, dtype=np.float64)
    for hx, hy, s, h in HILLS:
        z += h * np.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * s * s))
    # gentle rolling noise
    z += 4.0 * np.sin(x / 1900.0 + 0.3) * np.cos(y / 1500.0 - 0.7)
    z += 3.0 * np.sin(x / 700.0 - 1.1) * np.sin(y / 900.0 + 0.4)
    z += 2.0 * np.cos(x / 350.0 + y / 420.0)
    return z
