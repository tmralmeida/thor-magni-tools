import numpy as np


def pairwise_distances(points):
    x, y = points[:, 0], points[:, 1]
    return np.sqrt((x[:, None] - x) ** 2 + (y[:, None] - y) ** 2)
