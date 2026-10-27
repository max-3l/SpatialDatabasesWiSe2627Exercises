"""Utility functions for the spatial indices exercise."""

import heapq
from collections.abc import Callable

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from ipympl.backend_nbagg import Canvas, FigureManager
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle
from matplotlib.path import Path
from matplotlib.widgets import RectangleSelector

rng = np.random.default_rng(0)

# MARK: outline
# (lon, lat), clockwise from the Danish border.
GERMANY = np.array([
    (8.52, 54.88), (9.91, 54.80), (9.55, 54.51), (10.03, 54.67), (10.13, 54.31),
    (11.13, 54.39), (10.89, 53.96), (11.45, 53.90), (12.52, 54.48), (14.22, 53.93),
    (13.81, 53.86), (14.28, 53.74), (14.12, 52.84), (14.64, 52.58), (14.93, 50.99),
    (14.29, 51.05), (12.09, 50.26), (12.66, 49.43), (13.84, 48.78), (12.75, 48.12),
    (13.01, 47.47), (12.25, 47.74), (11.27, 47.39), (10.43, 47.59), (10.17, 47.27),
    (9.04, 47.82), (7.67, 47.54), (8.23, 48.97), (6.35, 49.46), (5.96, 51.82),
    (7.07, 52.24), (6.68, 52.56), (7.26, 53.00), (7.16, 53.63), (8.02, 53.71),
    (8.25, 53.40), (8.61, 53.88), (9.10, 53.86),
])
GERMANY_PATH = Path(GERMANY)

LON_MIN, LAT_MIN = GERMANY.min(axis=0)
LON_MAX, LAT_MAX = GERMANY.max(axis=0)


def inside_germany(lat, lon):
    return GERMANY_PATH.contains_points(np.c_[lon, lat])


# MARK: sampling
# name: (lat, lon, population in millions, approx.)
CITIES = {
    "Berlin": (52.52, 13.40, 3.7), "Hamburg": (53.55, 9.99, 1.9),
    "München": (48.14, 11.58, 1.5), "Köln": (50.94, 6.96, 1.1),
    "Frankfurt": (50.11, 8.68, 0.77), "Stuttgart": (48.78, 9.18, 0.63),
    "Düsseldorf": (51.23, 6.78, 0.62), "Leipzig": (51.34, 12.37, 0.62),
    "Dortmund": (51.51, 7.47, 0.59), "Essen": (51.46, 7.01, 0.58),
    "Bremen": (53.08, 8.80, 0.57), "Dresden": (51.05, 13.74, 0.56),
}
LAT, LON, POP = map(np.array, zip(*CITIES.values()))


def sample_background(n, rng=rng):
    """Uniform points inside the outline (rejection sampling)."""
    out = np.empty((0, 2))
    while len(out) < n:
        lat = rng.uniform(LAT_MIN, LAT_MAX, 2 * n)
        lon = rng.uniform(LON_MIN, LON_MAX, 2 * n)
        keep = inside_germany(lat, lon)
        out = np.vstack([out, np.c_[lat[keep], lon[keep]]])
    return out[:n]


def sample(n, background=0.15, k=6.0, rng=rng):
    """Return (n, 2) array of (lat, lon)."""
    w = POP / POP.sum()
    sigma_km = k * np.sqrt(POP)            # Berlin ≈ 12 km, Dresden ≈ 4.5 km
    n_bg = rng.binomial(n, background)
    idx = rng.choice(len(w), size=n - n_bg, p=w)
    dlat = rng.normal(0, sigma_km[idx] / 111)
    dlon = rng.normal(0, sigma_km[idx] / (111 * np.cos(np.radians(LAT[idx]))))
    pts = np.c_[LAT[idx] + dlat, LON[idx] + dlon]
    return np.vstack([pts, sample_background(n_bg, rng)])


MAX = 2**16 - 1
KM_PER_DEG = 111.32
LAT_REF = (LAT_MIN + LAT_MAX) / 2                      # ≈ 51°, for the lon scale
HEIGHT_KM = (LAT_MAX - LAT_MIN) * KM_PER_DEG           # Germany's max y extent
UNITS_PER_KM = MAX / HEIGHT_KM                         # same scale on both axes


def to_uint16(pts):
    """(lat, lon) -> (x, y) integers, y growing northward.

    Germany's north-south extent maps to 0..65535; x uses the same units per km,
    so proportions are kept and x only reaches about 47,000.
    """
    x_km = (pts[:, 1] - LON_MIN) * KM_PER_DEG * np.cos(np.radians(LAT_REF))
    y_km = (pts[:, 0] - LAT_MIN) * KM_PER_DEG
    xy = np.c_[x_km, y_km] * UNITS_PER_KM
    return np.clip(np.rint(xy), 0, MAX).astype(np.uint16)


def generate_city_data(n, seed=None):
    """Sample n city points as (x, y) tuples of Python ints on the uint16 grid.

    Python ints (not numpy.uint16) so the curve functions can use int.bit_length().
    """
    pts = to_uint16(sample(n, rng=np.random.default_rng(seed)))
    return [(int(x), int(y)) for x, y in pts]



# MARK: plotting
POINT_COLOR = "#2a6fdb"


def outline_patch(xy):
    return Polygon(xy, closed=True, facecolor="#f2f2f2", edgecolor="#555555",
                   lw=1.0, zorder=1)


def plot(pts_latlon, pts_u16, out="germany_points.png"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 8.5), constrained_layout=True)

    # Left: geographic coordinates, aspect corrected so Germany isn't stretched.
    ax1.add_patch(outline_patch(GERMANY))
    ax1.scatter(pts_latlon[:, 1], pts_latlon[:, 0], s=1, alpha=0.25,
                color=POINT_COLOR, linewidths=0, zorder=3, rasterized=True)
    ax1.scatter(LON, LAT, s=12, color="black", zorder=4)
    for name, (la, lo, _) in CITIES.items():
        dx, ha = (-4, "right") if name in ("Essen", "Düsseldorf", "Köln") else (4, "left")
        ax1.annotate(name, (lo, la), xytext=(dx, 3), textcoords="offset points",
                     ha=ha, fontsize=8, color="#222222", zorder=5)
    ax1.set_aspect(1 / np.cos(np.radians(LAT_REF)))
    ax1.set_xlim(LON_MIN - 0.3, LON_MAX + 0.3)
    ax1.set_ylim(LAT_MIN - 0.2, LAT_MAX + 0.2)
    ax1.set_xlabel("Longitude (°E)")
    ax1.set_ylabel("Latitude (°N)")
    ax1.set_title(f"{len(pts_latlon):,} sampled points (lat/lon)")

    # Right: the uint16 grid, with the outline mapped the same way.
    ax2.add_patch(outline_patch(to_uint16(GERMANY[:, ::-1]).astype(float)))
    ax2.scatter(pts_u16[:, 0], pts_u16[:, 1], s=1, alpha=0.25,
                color=POINT_COLOR, linewidths=0, zorder=3, rasterized=True)
    ax2.set_xlim(0, MAX)
    ax2.set_ylim(0, MAX)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x (uint16)")
    ax2.set_ylabel("y (uint16)")
    ax2.set_title("Normalized: Germany's height = 0 … 65535")

    for ax in (ax1, ax2):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    fig.savefig(out, dpi=150)
    plt.show()




# MARK: exercise plots
SIZE = 2**16
quadrant_size = SIZE // 4
quadrant_borders = [0, quadrant_size, 2 * quadrant_size, 3 * quadrant_size, 4 * quadrant_size]


def quadrant(p: tuple[int, int]) -> tuple[int, int]:
    return p[0] // quadrant_size, p[1] // quadrant_size


def measure_euclidean_distance(p1: tuple[int, int], p2: tuple[int, int]) -> float:
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def plot_spatial_curve(curve: Callable[[int, int], int], max_x: int = 256, max_y: int = 256, title: str = "Spatial Curve",
                       ylim: tuple[int, int] | None = None):
    """Plot the order in which the given curve visits the points of a max_x x max_y grid."""
    z_curve_points = []
    for x in range(max_x):
        for y in range(max_y):
            z_index = curve(x, y)
            z_curve_points.append((z_index, (x, y)))

    z_curve_points.sort(key=lambda p: p[0])

    sorted_coords = [p[1] for p in z_curve_points]

    plt.figure(figsize=(10, 5))
    plt.plot([coord[0] for coord in sorted_coords], [coord[1] for coord in sorted_coords], marker='o')
    plt.title(title)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.xlim(0, max_x-1)
    plt.ylim(*(ylim or (0, max_y-1)))
    plt.grid()


def plot_dataset(dataset: set[tuple[int, int]], query_points: set[tuple[int, int]]):
    plt.figure(figsize=(7, 7))
    plt.plot(*zip(*dataset), marker='o', markersize=2, linestyle='', color='#2a78d6', label='Dataset Points')
    plt.plot(*zip(*query_points), marker='x', markersize=8, linestyle='', color='#eb6834', label='Query Points')
    plt.xticks(quadrant_borders); plt.yticks(quadrant_borders)
    plt.xlim(0, SIZE); plt.ylim(0, SIZE)
    plt.grid()
    plt.legend()


index_cmap = LinearSegmentedColormap.from_list("curve_index", ["#0073ff", "#52d62a", "#a6341d"])


def plot_curve_index(dataset: set[tuple[int, int]], curves: dict[str, Callable[[int, int], int]]):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), layout="constrained")
    for ax, (name, curve) in zip(axes, curves.items()):
        points = list(dataset)
        scatter = ax.scatter(*zip(*points), c=[curve(x, y) for x, y in points], cmap=index_cmap, vmin=0, vmax=SIZE**2, s=4)
        ax.set_title(name)
        ax.set_aspect('equal')
        ax.set_xticks(quadrant_borders); ax.set_yticks(quadrant_borders)
        ax.set_xlim(0, SIZE); ax.set_ylim(0, SIZE)
        ax.grid()
    fig.colorbar(scatter, ax=axes, label='Curve index', shrink=0.8)


def plot_distance_pairs(dataset: set[tuple[int, int]], query_points: set[tuple[int, int]],
                        curves: dict[str, Callable[[int, int], int]], k: int = 16):
    pairs = [(q, p) for q in query_points
             for p in heapq.nsmallest(k, dataset, key=lambda p: measure_euclidean_distance(q, p))]

    _, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True, layout="constrained")
    for ax, (name, curve) in zip(axes, curves.items()):
        for crosses_border, label, color in [(False, "Same quadrant", "#2a78d6"), (True, "Different quadrants", "#eb6834")]:
            selected = [(q, p) for q, p in pairs if (quadrant(q) != quadrant(p)) == crosses_border]
            ax.scatter([measure_euclidean_distance(q, p) for q, p in selected],
                       [abs(curve(*q) - curve(*p)) for q, p in selected],
                       s=8, alpha=0.6, color=color, label=label)
        reference = [1, 4096]
        ax.plot(reference, [d**2 for d in reference], color='#6b6b6b', linewidth=1.5, linestyle='--', label='Curve distance = euclidean distance²')
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_title(name)
        ax.set_xlabel("Euclidean distance")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Curve distance |index(q) - index(p)|")
    axes[0].legend()


occupancy_cmap = LinearSegmentedColormap.from_list("occupancy", ["#cde2fb", "#2a78d6", "#0d366b"])


def partition_borders(low: int, high: int, divisions: int) -> list[int]:
    """Integer borders that split [low, high] into equally wide cells, cell i holds borders[i] <= v < borders[i + 1]."""
    width = high + 1 - low
    return [low + -(-i * width // divisions) for i in range(divisions + 1)]


def interactive_figure(**kwargs) -> Figure:
    """A figure that ipympl draws as an interactive widget, while all other plots of the notebook stay inline."""
    figure = Figure(**kwargs)
    FigureManager(Canvas(figure), num=0)
    figure.canvas.header_visible = False
    return figure


class IndexComparisonPlot:
    """Interactive comparison of the UniformGridIndex with the ZCurveIndex: a slider sets the divisions per
    axis, dragging on one of the lower maps draws the query rectangle on both."""

    def __init__(self, dataset: set[tuple[int, int]], grid_index_class: type, z_index_class: type,
                 divisions_per_axis: int = 8, query: tuple[int, int, int, int] = (2_000, 12_000, 29_000, 40_000)):
        self.dataset = dataset
        self.grid_index_class = grid_index_class
        self.z_index = z_index_class(dataset)
        self.z_keys = {p: self.z_index.curve(*p) for p in dataset}
        self.query = query

        self.fig = interactive_figure(figsize=(10, 9.2), dpi=90, layout="constrained")  # ipympl does not shrink figures to the viewport
        (self.cell_ax, self.curve_ax), (self.partition_ax, self.z_ax) = self.fig.subplots(2, 2)
        self.query_artists = {self.partition_ax: [], self.z_ax: []}
        # The selectors clip their rectangle to the axes limits, so they have to be set first.
        for ax in self.fig.axes:
            ax.set_aspect("equal")
            ax.set_xlim(0, SIZE); ax.set_ylim(0, SIZE)

        self.colorbar = self.fig.colorbar(self.draw_partition(divisions_per_axis), ax=self.cell_ax, shrink=0.8,
                                          label="Points per cell")
        keys = self.curve_ax.scatter(*zip(*self.z_keys), c=list(self.z_keys.values()), cmap=index_cmap, vmin=0, vmax=SIZE**2, s=2)
        self.fig.colorbar(keys, ax=self.curve_ax, shrink=0.8, label="Z-curve index")
        self.curve_ax.set_title("Z-curve index of every point\n", fontsize=9)

        self.selectors = [self.make_selector(ax) for ax in (self.partition_ax, self.z_ax)]
        for selector in self.selectors:
            selector.extents = query
        self.draw_queries()

        self.slider = widgets.IntSlider(value=divisions_per_axis, min=1, max=64, description="Divisions per axis",
                                        continuous_update=False, style={"description_width": "130px"},
                                        layout=widgets.Layout(width="500px"))
        self.slider.observe(self.on_divisions_change, names="value")

    def _repr_mimebundle_(self, **kwargs):
        return widgets.VBox([self.slider, self.fig.canvas])._repr_mimebundle_(**kwargs)

    def make_selector(self, ax) -> RectangleSelector:
        selector = RectangleSelector(ax, lambda press, release: self.on_select(selector), interactive=True,
                                     button=[1], minspanx=SIZE / 200, minspany=SIZE / 200,
                                     props=dict(fill=False, edgecolor="#222222", linestyle="--", linewidth=1.5))
        return selector

    def on_select(self, source: RectangleSelector):
        """Take the query rectangle from the selector that was dragged and show it on the other map as well."""
        xmin, xmax, ymin, ymax = source.extents
        # A click without dragging removes the rectangle, its extents are then below the minimal span.
        if xmax - xmin <= source.minspanx or ymax - ymin <= source.minspany:
            self.query = None
        else:
            self.query = (max(round(xmin), 0), min(round(xmax), SIZE - 1), max(round(ymin), 0), min(round(ymax), SIZE - 1))
        for selector in self.selectors:
            if selector is source:
                continue
            if self.query is None:
                selector.clear()
            else:
                selector.set_visible(True)
                selector.extents = source.extents
        self.draw_queries()

    def on_divisions_change(self, change):
        self.colorbar.update_normal(self.draw_partition(change.new))
        self.draw_queries()

    def cell_rectangle(self, i: int, j: int, **kwargs) -> Rectangle:
        return Rectangle((self.x_borders[i], self.y_borders[j]), self.x_borders[i + 1] - self.x_borders[i],
                         self.y_borders[j + 1] - self.y_borders[j], **kwargs)

    def draw_grid(self, ax) -> list:
        if self.divisions_per_axis > 32:  # cell borders become noise on finer grids
            return []
        return [ax.vlines(self.x_borders, self.y_borders[0], self.y_borders[-1], color="#9a9a9a", linewidth=0.5),
                ax.hlines(self.y_borders, self.x_borders[0], self.x_borders[-1], color="#9a9a9a", linewidth=0.5)]

    def draw_partition(self, divisions_per_axis: int):
        """Build the index and plot the content of every cell as returned by points_in_rectangle."""
        self.divisions_per_axis = divisions_per_axis
        self.index = self.grid_index_class(self.dataset, divisions_per_axis)
        xs, ys = zip(*self.dataset)
        self.x_borders = partition_borders(min(xs), max(xs), divisions_per_axis)
        self.y_borders = partition_borders(min(ys), max(ys), divisions_per_axis)
        self.cells = [(i, j) for i in range(divisions_per_axis) for j in range(divisions_per_axis)]

        self.cell_points = {cell: set() for cell in self.cells}
        for x, y in self.dataset:
            self.cell_points[(x - self.x_borders[0]) * divisions_per_axis // (self.x_borders[-1] - self.x_borders[0]),
                             (y - self.y_borders[0]) * divisions_per_axis // (self.y_borders[-1] - self.y_borders[0])].add((x, y))
        # Unfinished methods return None, which is treated as an empty result.
        found = {(i, j): set(self.index.points_in_rectangle(self.x_borders[i], self.x_borders[i + 1] - 1,
                                                            self.y_borders[j], self.y_borders[j + 1] - 1) or [])
                 for i, j in self.cells}
        wrong_cells = [cell for cell in self.cells if found[cell] != self.cell_points[cell]]
        has_point_hits = sum(bool(self.index.has_point(p)) for p in self.dataset)

        ax = self.cell_ax
        ax.clear()
        counts = [[len(found[i, j]) or float("nan") for i in range(divisions_per_axis)] for j in range(divisions_per_axis)]
        fullest = max(len(points) for points in found.values())
        mesh = ax.pcolormesh(self.x_borders, self.y_borders, counts, cmap=occupancy_cmap, norm=LogNorm(vmin=1, vmax=max(fullest, 10)))
        for cell in wrong_cells:
            ax.add_patch(self.cell_rectangle(*cell, fill=False, edgecolor="#d62728", linewidth=1.5))
        self.draw_grid(ax)
        empty = sum(not points for points in found.values()) / len(self.cells)
        ax.set_title(f"{divisions_per_axis}x{divisions_per_axis} cells: {empty:.0%} empty, fullest holds {fullest} points\n"
                     f"{len(wrong_cells)} wrong cells, has_point finds {has_point_hits} of {len(self.dataset)} points", fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlim(0, SIZE); ax.set_ylim(0, SIZE)
        return mesh

    def draw_queries(self):
        """Run the range query of the selected rectangle on both indexes and plot what they inspect and return."""
        if self.query is None:
            self.draw_query(self.partition_ax, "Drag on the map to draw a query rectangle\n", artists=self.draw_grid(self.partition_ax))
            self.draw_query(self.z_ax, "Drag on the map to draw a query rectangle\n")
            return
        xlow, xhigh, ylow, yhigh = self.query
        inside = {p for p in self.dataset if xlow <= p[0] <= xhigh and ylow <= p[1] <= yhigh}

        touched = [(i, j) for i, j in self.cells if self.x_borders[i] <= xhigh and xlow < self.x_borders[i + 1]
                   and self.y_borders[j] <= yhigh and ylow < self.y_borders[j + 1]]
        inspected = set().union(*(self.cell_points[cell] for cell in touched))
        result = set(self.index.points_in_rectangle(xlow, xhigh, ylow, yhigh) or [])
        self.draw_query(self.partition_ax,
                        f"Grid index inspects {len(inspected)} points in {len(touched)} of {len(self.cells)} cells\n"
                        f"{len(result)} returned: {len(inside - result)} missing, {len(result - inside)} wrong",
                        inspected, result, inside,
                        [self.partition_ax.add_patch(self.cell_rectangle(*cell, color="#cde2fb", linewidth=0)) for cell in touched]
                        + self.draw_grid(self.partition_ax))

        low_key, high_key = self.z_index.curve(xlow, ylow), self.z_index.curve(xhigh, yhigh)
        inspected = {p for p, key in self.z_keys.items() if low_key <= key <= high_key}
        result = set(self.z_index.points_in_rectangle(xlow, xhigh, ylow, yhigh))
        self.draw_query(self.z_ax,
                        f"Z-curve index inspects {len(inspected)} points in its key range\n"
                        f"{len(result)} returned: {len(inside - result)} missing, {len(result - inside)} wrong",
                        inspected, result, inside)

    def draw_query(self, ax, title: str, inspected=frozenset(), result=frozenset(), inside=frozenset(), artists=()):
        for artist in self.query_artists[ax]:
            artist.remove()
        self.query_artists[ax] = list(artists)
        for points, style in [(self.dataset - inspected - result - inside, dict(s=2, color="#9a9a9a", label="Dataset points")),
                              (inspected - result - inside, dict(s=2, color="#2a78d6", label="Inspected points")),
                              (result & inside, dict(s=4, color="#eb6834", label="Returned points")),
                              (inside - result, dict(s=16, marker="x", color="#d62728", label="Missing points")),
                              (result - inside, dict(s=16, marker="x", color="#7c3aed", label="Wrongly returned points"))]:
            if points:
                self.query_artists[ax].append(ax.scatter(*zip(*points), **style))
        ax.set_title(title, fontsize=9)
        ax.legend(loc="upper right", fontsize="small")
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    pts = sample(100_000)
    plot(pts, to_uint16(pts))