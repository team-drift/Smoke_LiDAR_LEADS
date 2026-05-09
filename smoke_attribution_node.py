import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
import struct
import math

class SmokeAttributionNode(Node):
    def __init__(self):
        super().__init__('smoke_attribution_node')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/lidar/points',
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(
            PointCloud2,
            '/lidar/points_attributed',
            10)
        self.get_logger().info("Smoke attribution node started.")
        
        self.SMOKE_X_MIN = 1.0
        self.SMOKE_X_MAX = 3.0
        self.SMOKE_Y_MIN = -1.0
        self.SMOKE_Y_MAX = 1.0

    def listener_callback(self, msg):
        point_step = msg.point_step
        data = msg.data
        num_points = msg.width * msg.height
        
        offset_x = next(f.offset for f in msg.fields if f.name == 'x')
        offset_y = next(f.offset for f in msg.fields if f.name == 'y')
        offset_z = next(f.offset for f in msg.fields if f.name == 'z')
        
        new_fields = list(msg.fields)
        smoke_offset = msg.point_step
        new_fields.append(PointField(name='smoke', offset=smoke_offset, datatype=PointField.FLOAT32, count=1))
        
        new_point_step = msg.point_step + 4
        new_data = bytearray(num_points * new_point_step)
        
        smoke_points_count = 0
        
        for i in range(num_points):
            base = i * point_step
            new_base = i * new_point_step
            
            new_data[new_base:new_base+point_step] = data[base:base+point_step]
            
            x = struct.unpack_from('f', data, base + offset_x)[0]
            y = struct.unpack_from('f', data, base + offset_y)[0]
            z = struct.unpack_from('f', data, base + offset_z)[0]
            
            if math.isfinite(x) and math.isfinite(y) and math.isfinite(z):
                in_footprint = self.SMOKE_X_MIN <= x <= self.SMOKE_X_MAX and self.SMOKE_Y_MIN <= y <= self.SMOKE_Y_MAX
                smoke = 1.0 if in_footprint else 0.0
                if smoke > 0:
                    smoke_points_count += 1
            else:
                smoke = 0.0
                
            struct.pack_into('f', new_data, new_base + smoke_offset, smoke)
            
        new_msg = PointCloud2()
        new_msg.header = msg.header
        new_msg.height = msg.height
        new_msg.width = msg.width
        new_msg.fields = new_fields
        new_msg.is_bigendian = msg.is_bigendian
        new_msg.point_step = new_point_step
        new_msg.row_step = new_point_step * msg.width
        new_msg.data = bytes(new_data)
        new_msg.is_dense = msg.is_dense
        
        self.publisher.publish(new_msg)
        
        if not hasattr(self, 'frame_count'):
            self.frame_count = 0
        self.frame_count += 1
        
        if self.frame_count % 10 == 0:
            self.get_logger().info(f"Published frame {self.frame_count}: {smoke_points_count}/{num_points} points labeled as smoke.")

def main(args=None):
    rclpy.init(args=args)
    node = SmokeAttributionNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
