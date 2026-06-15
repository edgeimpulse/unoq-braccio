import math

from unoq_braccio_driver.braccio_model import JOINT_NAMES, clamp_degrees


UPPER_ARM_M = 0.14
FOREARM_M = 0.13
WRIST_M = 0.075


def solve_planar_braccio(x_m: float, y_m: float, z_m: float, gripper: int) -> list[int]:
    base = math.degrees(math.atan2(y_m, x_m)) + 90.0
    horizontal = math.hypot(x_m, y_m)
    shoulder_height = 0.11
    wrist_target = max(0.04, horizontal - WRIST_M)
    vertical = z_m - shoulder_height
    reach = math.hypot(wrist_target, vertical)
    reach = max(0.035, min(UPPER_ARM_M + FOREARM_M - 0.01, reach))

    cos_elbow = (
        reach * reach - UPPER_ARM_M * UPPER_ARM_M - FOREARM_M * FOREARM_M
    ) / (2.0 * UPPER_ARM_M * FOREARM_M)
    cos_elbow = max(-1.0, min(1.0, cos_elbow))
    elbow_inner = math.acos(cos_elbow)

    target_angle = math.atan2(vertical, wrist_target)
    shoulder_offset = math.atan2(
        FOREARM_M * math.sin(elbow_inner),
        UPPER_ARM_M + FOREARM_M * math.cos(elbow_inner),
    )

    shoulder_world = target_angle + shoulder_offset
    elbow_world = elbow_inner - math.pi
    wrist_world = -(shoulder_world + elbow_world)

    return [
        clamp_degrees("base", base),
        clamp_degrees("shoulder", 90.0 - math.degrees(shoulder_world)),
        clamp_degrees("elbow", 90.0 + math.degrees(elbow_world)),
        clamp_degrees("wrist_vertical", 90.0 + math.degrees(wrist_world)),
        90,
        clamp_degrees("gripper", gripper),
    ]


def create_node_class():
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState

    class IkPoseDemo(Node):
        def __init__(self) -> None:
            super().__init__("unoq_braccio_ik_pose_demo")
            self.declare_parameter("x", 0.30)
            self.declare_parameter("y", 0.0)
            self.declare_parameter("z", 0.06)
            self.declare_parameter("gripper", 25)
            self.publisher = self.create_publisher(JointState, "/braccio/joint_command", 10)
            self.timer = self.create_timer(0.5, self.publish_once)
            self.sent = False

        def publish_once(self) -> None:
            if self.sent:
                rclpy.shutdown()
                return

            pose = solve_planar_braccio(
                float(self.get_parameter("x").value),
                float(self.get_parameter("y").value),
                float(self.get_parameter("z").value),
                int(self.get_parameter("gripper").value),
            )

            msg = JointState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.name = JOINT_NAMES
            msg.position = [float(value) for value in pose]
            self.publisher.publish(msg)
            self.get_logger().info(f"Published IK pose: {pose}")
            self.sent = True

    return IkPoseDemo


class _IkPoseDemoPlaceholder:
    def __init__(self) -> None:
        raise RuntimeError("Use create_node_class() after rclpy is available")


IkPoseDemo = _IkPoseDemoPlaceholder


def main() -> None:
    import rclpy

    rclpy.init()
    node_class = create_node_class()
    node = node_class()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
