# Smoke and LiDAR

## Prereqs
- This is was on WSL or run it on Linux (Ubuntu)
- ROS 2 Jazzy (ROS 2 Jazzy Deskstop)
- Gazebo Harmonic (`gz-harmonic`) and the bridge (`ros_gz_bridge`)
- https://raw.githubusercontent.com/gazebosim/gz-sim/gz-sim8/examples/worlds/particle_emitter.sdf

---

## Directory Structure

```
smoke_demo/
└── smoke_lidar.sdf   'Smoke LiDAR Demo Readme.md'   particle_emitter.sdf
```

---

## Launch Instructions

Open **three separate terminals**:

---

### Terminal 1 — Gazebo Simulation

```bash
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="-r smoke_lidar.sdf"
```

The `lidar_model` should show up. In the Gazebo UI, click the 3 dots (top right), search for `Visualize Lidar`, click the orange refresh button, and blue lines should appear.

---

### Terminal 2 — RViz2

```bash
rviz2
```

RViz configurations:

| Setting            | Value                                      |
|--------------------|--------------------------------------------|
| **Fixed Frame**    | `lidar_model/lidar_link/gpu_lidar`         |
| **Add display**    | `By topic` -> `PointCloud2`                |
| **Add display**    | `By topic` -> `PointCloud2/lidar/points_attributed`|
| **Channel Name**   | `smoke`                                |
| **Size (m)**       | `0.5` or `0.1`                   |
| **Reliability Policy** | Best Effort                         |

---

### Terminal 3 — ROS–Gazebo Bridge

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked \
  --ros-args -r /lidar/points/points:=/lidar/points
```

This command bridges the Gazebo topic `/lidar/points/points` to the ROS topic `/lidar/points`.

---

### Terminal 4 — Smoke Attribution Node

```bash
python3 smoke_attribution_node.py
```

---

### Terminal 5 — Visibility Scorer Node

```bash
python3 visibility_scorer.py
```
This node checks the LiDAR points hitting the target box, calculates if those specific rays passed through the smoke footprint, and outputs a live visibility classification (Visible, Partially Occluded, or Fully Occluded).

---

### Run the Entire Pipeline (One-Click)

Instead of opening 5 different terminals, you can now run the entire pipeline with a single script! This will launch Gazebo, the ROS Bridge, RViz, the attribution node, and the visibility scorer all at once.

```bash
./run_pipeline.sh
```

To stop all nodes, press `Ctrl+C` in that terminal.