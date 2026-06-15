# Edge Impulse Integration

Use Edge Impulse to turn classifier labels into Braccio poses.

Recommended flow:

1. Build and train an Edge Impulse project.
2. Export the model for the device that will run inference.
3. Publish the top label as a ROS 2 string on `/edge_impulse/label`.
4. Run `edge_impulse_mapper` with `label_to_pose.yaml`.

Example:

```bash
ros2 run unoq_braccio_driver edge_impulse_mapper \
  --ros-args -p mapping_file:=edge_impulse/label_to_pose.yaml
```

Publish a simulated label:

```bash
ros2 topic pub --once /edge_impulse/label std_msgs/msg/String "{data: wave}"
```

For recording Braccio command and robot-status data as CSV, see
[data_capture.md](data_capture.md).
