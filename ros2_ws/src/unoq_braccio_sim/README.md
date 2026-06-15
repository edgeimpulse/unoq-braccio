# UNO Q Braccio Gazebo Simulation

This package provides a lightweight Gazebo Harmonic simulation for the UNO Q
Braccio project.

It includes:

- Six Braccio command joints: `base`, `shoulder`, `elbow`, `wrist_vertical`,
  `wrist_rotation`, and `gripper`.
- Visual STL meshes for the Braccio base, links, wrist, and gripper, adapted
  from Will Stedden's GPL-3.0 Braccio MoveIt/Gazebo package.
- A simple gripper-mounted camera body matching the real camera position above
  and between the fingers.
- Red, blue, and yellow pick blocks.
- Three colored drop zones.
- `ros2_control` metadata and controller configuration.
- A joint-state simulator fallback so `/braccio/joint_command` pose demos can
  move the model even without a full controller command bridge.
- A joint trajectory bridge that republishes `/braccio/joint_command` to
  `/arm_controller/joint_trajectory` for Gazebo controller use.

## Install Dependencies

On Ubuntu with ROS 2 Jazzy:

```bash
sudo apt update
sudo apt install \
  ros-jazzy-ros-gz \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-xacro
```

## Build

```bash
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Run

```bash
ros2 launch unoq_braccio_bringup sim.launch.py
```

Then publish a pose:

```bash
ros2 run unoq_braccio_driver pose_demo --ros-args -p pose:=ready
ros2 run unoq_braccio_driver pose_demo --ros-args -p pose:=pickup
ros2 run unoq_braccio_driver pose_demo --ros-args -p pose:=wave
```

You can also publish a simple x/y/z target through a constrained Braccio IK
helper:

```bash
ros2 run unoq_braccio_driver ik_pose_demo --ros-args \
  -p x:=0.30 -p y:=0.00 -p z:=0.06 -p gripper:=25
```

The helper uses a deliberately small 2D planar IK calculation for the shoulder,
elbow, and wrist, plus base rotation from `atan2(y, x)`. It is meant for quick
simulation targets and reach testing, not final calibrated motion planning.

## Current Scope

This is a practical development simulation, not a calibrated digital twin. Link
dimensions and inertias are approximate. The pick blocks and bins are there for
vision and workflow testing; grasp physics still needs tuning before relying on
it for realistic pick-and-place contact.

The launch starts both the controller bridge and the joint-state simulator. If
`gz_ros2_control` is available, the controller path drives
`/arm_controller/joint_trajectory`. If controller startup fails, the
joint-state simulator still publishes `/joint_states` so the model follows
project pose commands for visual testing.

## Reference

This simulation direction is inspired by Will Stedden's Braccio Gazebo/MoveIt
writeup, especially the practical point that the Braccio has a constrained
workspace and benefits from a simple 2D IK approach before full motion planning:

```text
https://opus.stedden.org/2020/08/braccio-moveit-gazebo/
```

That project targeted ROS Melodic and Gazebo Classic. This repository keeps the
same pick/drop playground idea but uses ROS 2 Jazzy and Gazebo Harmonic.

The Braccio STL visual meshes are copied from:

```text
https://github.com/lots-of-things/braccio_moveit_gazebo
```

Those mesh files are isolated under
`ros2_ws/src/unoq_braccio_sim/meshes/braccio_stedden/` with the original GPL-3.0
license text.
