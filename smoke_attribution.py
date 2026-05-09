import csv
import math
import os
import sys
import matplotlib.pyplot as plt


# Smoke emitter footprint from smoke_lidar.sdf:
# model pose = (2, 0, 0), emitter size = (2, 2, 0) -> x in [1, 3], y in [-1, 1].
SMOKE_X_MIN = 1.0
SMOKE_X_MAX = 3.0
SMOKE_Y_MIN = -1.0
SMOKE_Y_MAX = 1.0

PLOT_DIR = "lidar_plots"


def is_smoke_pass(x: float, y: float, z: float) -> int:
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        return 0
    in_footprint = SMOKE_X_MIN <= x <= SMOKE_X_MAX and SMOKE_Y_MIN <= y <= SMOKE_Y_MAX
    return 1 if in_footprint else 0


def plot_attribution(points, out_csv_path: str) -> None:

    smoke_x = []
    smoke_y = []
    smoke_z = []
    clear_x = []
    clear_y = []
    clear_z = []

    for x, y, z, smoke in points:
        if smoke == 1:
            smoke_x.append(x)
            smoke_y.append(y)
            smoke_z.append(z)
        else:
            clear_x.append(x)
            clear_y.append(y)
            clear_z.append(z)

    os.makedirs(PLOT_DIR, exist_ok=True)
    plot_name = os.path.basename(out_csv_path).replace(".csv", ".png")
    out_png_path = os.path.join(PLOT_DIR, plot_name)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    if clear_x:
        ax.scatter(clear_x, clear_y, clear_z, s=3, c="#8a8a8a", label="clear (0)", alpha=0.55)
    if smoke_x:
        ax.scatter(smoke_x, smoke_y, smoke_z, s=6, c="#d11f1f", label="smoke (1)", alpha=0.9)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title("LiDAR Smoke Attribution Validation\nClear vs Smoke-Labeled Points")
    ax.legend(loc="upper right")
    fig.savefig(out_png_path, dpi=150)
    plt.close(fig)
    print(f"Wrote {out_png_path}")


def process_file(csv_path: str) -> None:
    if csv_path.endswith("_attributed.csv"):
        return

    out_path = os.path.splitext(csv_path)[0] + "_attributed.csv"
    with open(csv_path, newline="") as in_fh, open(out_path, "w", newline="") as out_fh:
        reader = csv.DictReader(in_fh)

        fieldnames = list(reader.fieldnames)
        if "smoke" not in fieldnames:
            fieldnames.append("smoke")

        writer = csv.DictWriter(out_fh, fieldnames=fieldnames)
        writer.writeheader()

        smoke_count = 0
        total = 0
        points_for_plot = []
        for row in reader:
            x = float(row["x"])
            y = float(row["y"])
            z = float(row["z"])
            smoke = is_smoke_pass(x, y, z)
            row["smoke"] = smoke
            writer.writerow(row)
            smoke_count += smoke
            total += 1
            if math.isfinite(x) and math.isfinite(y) and math.isfinite(z):
                points_for_plot.append((x, y, z, smoke))

    print(f"Wrote {out_path} (smoke={smoke_count}/{total})")
    plot_attribution(points_for_plot, out_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 smoke_attribution.py lidar_logs/*.csv")
        sys.exit(1)

    for csv_path in sys.argv[1:]:
        process_file(csv_path)
