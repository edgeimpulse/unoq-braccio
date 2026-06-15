# Hardware Notes

## Wiring

Use the Braccio shield in its standard configuration. The firmware relies on the
official Braccio library pin assignments:

- M1: base
- M2: shoulder
- M3: elbow
- M4: wrist vertical
- M5: wrist rotation
- M6: gripper

Power the servos from the Braccio shield power input. Do not rely on USB power
for the arm.

## Conservative Joint Limits

The firmware and ROS driver clamp commands to:

| Joint | Min | Max | Rest |
| --- | ---: | ---: | ---: |
| base | 0 | 180 | 90 |
| shoulder | 15 | 165 | 45 |
| elbow | 0 | 180 | 180 |
| wrist_vertical | 0 | 180 | 180 |
| wrist_rotation | 0 | 180 | 90 |
| gripper | 10 | 73 | 10 |

Tune these values for your arm after validating mechanical clearance.
