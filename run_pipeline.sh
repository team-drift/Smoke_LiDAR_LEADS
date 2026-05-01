#!/bin/bash

echo "=========================================="
echo " Starting Smoke LiDAR LEADS Pipeline..."
echo "=========================================="

cleanup() {
    echo "Stopping all pipeline processes..."
    kill $SCORER_PID $ATTR_PID $RVIZ_PID $BRIDGE_PID $GAZEBO_PID 2>/dev/null
    echo "All processes stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "[1/5] Launching Gazebo..."
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="-r smoke_lidar.sdf" > gazebo.log 2>&1 &
GAZEBO_PID=$!
sleep 4

echo "[2/5] Launching ROS-Gazebo Bridge..."
ros2 run ros_gz_bridge parameter_bridge \
  /lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked \
  --ros-args -r /lidar/points/points:=/lidar/points > bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 2

echo "[3/5] Launching RViz2..."
rviz2 > rviz.log 2>&1 &
RVIZ_PID=$!
sleep 2

echo "[4/5] Launching Smoke Attribution Node..."
python3 smoke_attribution_node.py > attribution.log 2>&1 &
ATTR_PID=$!
sleep 2

echo "[5/5] Launching Visibility Scorer Node (Logging to Console & CSV)..."
python3 visibility_scorer.py &
SCORER_PID=$!

echo "=========================================="
echo " Pipeline is running! Press Ctrl+C to stop."
echo "=========================================="

wait