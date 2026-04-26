import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import struct
import math
import matplotlib.pyplot as plt
import os

class PlotCaptureNode(Node):
    def __init__(self):
        super().__init__('plot_capture_node')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/lidar/points_attributed',
            self.listener_callback,
            10)

    def listener_callback(self, msg):
        point_step = msg.point_step
        data = msg.data
        num_points = msg.width * msg.height
        
        offset_x = next(f.offset for f in msg.fields if f.name == 'x')
        offset_y = next(f.offset for f in msg.fields if f.name == 'y')
        offset_z = next(f.offset for f in msg.fields if f.name == 'z')
        smoke_offset = next(f.offset for f in msg.fields if f.name == 'smoke')
        
        smoke_x, smoke_y, smoke_z = [], [], []
        clear_x, clear_y, clear_z = [], [], []
        box_x, box_y, box_z = [], [], []
        
        for i in range(num_points):
            base = i * point_step
            x = struct.unpack_from('f', data, base + offset_x)[0]
            y = struct.unpack_from('f', data, base + offset_y)[0]
            z = struct.unpack_from('f', data, base + offset_z)[0]
            smoke = struct.unpack_from('f', data, base + smoke_offset)[0]
            
            if math.isfinite(x) and math.isfinite(y) and math.isfinite(z):
                if smoke > 0.5:
                    smoke_x.append(x)
                    smoke_y.append(y)
                    smoke_z.append(z)
                elif 3.4 <= x <= 4.6 and -0.6 <= y <= 0.6 and z >= 0.0:
                    box_x.append(x)
                    box_y.append(y)
                    box_z.append(z)
                else:
                    clear_x.append(x)
                    clear_y.append(y)
                    clear_z.append(z)
                    
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        if clear_x:
            ax.scatter(clear_x, clear_y, clear_z, s=5, label='Clear Ground')
        if smoke_x:
            ax.scatter(smoke_x, smoke_y, smoke_z, s=15, label='Smoke Footprint')
        if box_x:
            ax.scatter(box_x, box_y, box_z, s=20, label='Target Box')
            
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title('LiDAR Attribution Validation (with Target Box)')
        ax.legend()
                
        out_path = 'target_box_validation.png'
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
                
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = PlotCaptureNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
