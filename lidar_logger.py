import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import os
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
        self.get_logger().info(f"Logging to {self.log_dir}/ ...")

    def listener_callback(self, msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        dt = datetime.fromtimestamp(stamp)
        frame_id = msg.header.frame_id.replace('/', '_')
        filename = f"{dt.strftime('%Y%m%d_%H%M%S_%f')}_{frame_id}.bin"
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(bytes(msg.data))
        self.get_logger().info(f"Saved {filepath}")

def main(args=None):
    rclpy.init(args=args)
    node = LidarLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
