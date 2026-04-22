import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import os
import math
from datetime import datetime

class LidarLogger(Node):
    def __init__(self):
        super().__init__('lidar_logger')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/lidar/points',
            self.listener_callback,
            10)
        self.log_dir = 'lidar_logs'
        os.makedirs(self.log_dir, exist_ok=True)
        self.plot_dir = 'lidar_plots'
        os.makedirs(self.plot_dir, exist_ok=True)
        self.get_logger().info(f"Logging to {self.log_dir}/ ...")
        self.file_count = 0
        self.max_files = 10
        self._stop_logged = False

    def _plot_csv(self, csv_path, title):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self.get_logger().warning("matplotlib not found; skipping plot generation.")
            return

        xs = []
        ys = []
        zs = []
        with open(csv_path, 'r', newline='') as f:
            next(f, None)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 3:
                    continue
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                except ValueError:
                    continue
                if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
                    continue
                xs.append(x)
                ys.append(y)
                zs.append(z)

        if not xs:
            self.get_logger().warning(f"No finite points in {csv_path}; skipping plot.")
            return

        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xs, ys, zs, s=1)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(title)
        out_png = os.path.join(self.plot_dir, os.path.basename(csv_path).replace('.csv', '.png'))
        fig.savefig(out_png, dpi=140)
        plt.close(fig)
        self.get_logger().info(f"Saved plot {out_png}")

    def listener_callback(self, msg):
        if self.file_count >= self.max_files:
            if not self._stop_logged:
                self.get_logger().info(f"Reached {self.max_files} files, stopping logger.")
                self._stop_logged = True
                rclpy.shutdown()
            return
        import csv
        import struct
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        dt = datetime.fromtimestamp(stamp)
        frame_id = msg.header.frame_id.replace('/', '_')
        filename = f"{dt.strftime('%Y%m%d_%H%M%S_%f')}_{frame_id}.csv"
        filepath = os.path.join(self.log_dir, filename)

        def read_points(msg):
            field_names = [f.name for f in msg.fields]
            has_intensity = 'intensity' in field_names
            point_step = msg.point_step
            data = msg.data
            num_points = msg.width * msg.height
            offset_x = next(f.offset for f in msg.fields if f.name == 'x')
            offset_y = next(f.offset for f in msg.fields if f.name == 'y')
            offset_z = next(f.offset for f in msg.fields if f.name == 'z')
            offset_i = next((f.offset for f in msg.fields if f.name == 'intensity'), None)
            for i in range(num_points):
                base = i * point_step
                x = struct.unpack_from('f', data, base + offset_x)[0]
                y = struct.unpack_from('f', data, base + offset_y)[0]
                z = struct.unpack_from('f', data, base + offset_z)[0]
                if offset_i is not None:
                    intensity = struct.unpack_from('f', data, base + offset_i)[0]
                    yield (x, y, z, intensity)
                else:
                    yield (x, y, z)

        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['x', 'y', 'z']
            if any(f.name == 'intensity' for f in msg.fields):
                fieldnames.append('intensity')
            fieldnames += ['timestamp', 'frame_id']
            writer = csv.writer(csvfile)
            writer.writerow(fieldnames)
            for pt in read_points(msg):
                row = list(pt) + [stamp, msg.header.frame_id]
                writer.writerow(row)
        self.get_logger().info(f"Saved {filepath}")
        self._plot_csv(filepath, f"LiDAR PointCloud: {os.path.basename(filepath)}")
        self.file_count += 1

def main(args=None):
    rclpy.init(args=args)
    node = LidarLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
