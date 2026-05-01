import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import struct
import math
import csv
import time

class VisibilityScorerNode(Node):
    def __init__(self):
        super().__init__('visibility_scorer_node')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/lidar/points_attributed',
            self.listener_callback,
            10)
        
        # Smoke volume definition (same as attribution node)
        self.SMOKE_X_MIN = 1.0
        self.SMOKE_X_MAX = 3.0
        self.SMOKE_Y_MIN = -1.0
        self.SMOKE_Y_MAX = 1.0
        
        self.boxes = {
            'Box_1_Outside': {'x_min': 3.5, 'x_max': 4.5, 'y_min': 4.5, 'y_max': 5.5},
            'Box_2_In_Smoke': {'x_min': 3.5, 'x_max': 4.5, 'y_min': -0.5, 'y_max': 0.5},
            'Box_3_Behind_Box_2': {'x_min': 5.5, 'x_max': 6.5, 'y_min': 0.25, 'y_max': 1.25}
        }

        self.csv_file = open('visibility_log.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Timestamp', 'Box_Name', 'Total_Points', 'Clear_Points', 'Through_Smoke_Points', 'Status'])

        self.get_logger().info("Visibility Scorer Node started. Waiting for data...")

    def ray_passes_through_smoke(self, px, py):
        """Check if a ray from origin (0,0) to point (px, py) passes through the smoke volume."""
        if px < self.SMOKE_X_MIN:
            return False
        # Project the ray to the front and back faces of the smoke volume
        # At the front face (x = SMOKE_X_MIN), what is y?
        y_at_front = (py / px) * self.SMOKE_X_MIN
        # At the back face (x = SMOKE_X_MAX), what is y?
        y_at_back = (py / px) * self.SMOKE_X_MAX
        # The ray passes through if y is within bounds at either face
        y_min_at_front = min(y_at_front, y_at_back)
        y_max_at_front = max(y_at_front, y_at_back)
        # Check for overlap between [y_min_at_front, y_max_at_front] and [SMOKE_Y_MIN, SMOKE_Y_MAX]
        if y_max_at_front < self.SMOKE_Y_MIN or y_min_at_front > self.SMOKE_Y_MAX:
            return False
        return True

    def listener_callback(self, msg):
        point_step = msg.point_step
        data = msg.data
        num_points = msg.width * msg.height
        
        # Get field offsets
        offset_x = next(f.offset for f in msg.fields if f.name == 'x')
        offset_y = next(f.offset for f in msg.fields if f.name == 'y')
        offset_z = next(f.offset for f in msg.fields if f.name == 'z')
        
        # Stats: total hits on the box, and how many rays passed through smoke
        stats = {name: {'total': 0, 'through_smoke': 0} for name in self.boxes}
        
        for i in range(num_points):
            base = i * point_step
            x = struct.unpack_from('f', data, base + offset_x)[0]
            y = struct.unpack_from('f', data, base + offset_y)[0]
            z = struct.unpack_from('f', data, base + offset_z)[0]
            
            if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
                continue
            if z < 0.1:  # Ignore the ground
                continue
            
            # Check which box this point belongs to
            for name, bounds in self.boxes.items():
                if (bounds['x_min'] <= x <= bounds['x_max'] and 
                    bounds['y_min'] <= y <= bounds['y_max']):
                    stats[name]['total'] += 1
                    # Check if the ray to this point passed through smoke
                    if self.ray_passes_through_smoke(x, y):
                        stats[name]['through_smoke'] += 1
        
        timestamp = time.time()
        
        log_str = "--- Visibility Report ---\n"
        for name, s in stats.items():
            total = s['total']
            through_smoke = s['through_smoke']
            clear_hits = total - through_smoke
            
            if total == 0:
                status = "Not Detected"
            elif through_smoke == 0:
                status = "Clear"
            elif clear_hits > 0:
                status = f"Partially Degraded ({clear_hits} clear, {through_smoke} through smoke)"
            else:
                status = "Visible Through Smoke"
                    
            log_str += f"{name}: {status} ({total} hits, {clear_hits} clear, {through_smoke} through smoke)\n"
            self.csv_writer.writerow([timestamp, name, total, clear_hits, through_smoke, status])
            
        self.get_logger().info("\n" + log_str)
        self.csv_file.flush()

def main(args=None):
    rclpy.init(args=args)
    node = VisibilityScorerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.csv_file.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
