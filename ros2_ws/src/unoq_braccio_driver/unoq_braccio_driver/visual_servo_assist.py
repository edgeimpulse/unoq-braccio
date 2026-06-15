import re

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from unoq_braccio_driver.braccio_model import JOINT_NAMES, POSES, clamp_degrees


STAT_PATTERN = re.compile(r"target=([0-9,\-]+)")
VISION_PATTERN = re.compile(r"x_norm=([\-0-9.]+).*y_norm=([\-0-9.]+)")


class VisualServoAssist(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_visual_servo_assist")
        self.declare_parameter("enabled", False)
        self.declare_parameter("deadband", 0.12)
        self.declare_parameter("base_gain_deg", -4.0)
        self.declare_parameter("shoulder_gain_deg", -3.0)
        self.declare_parameter("max_step_deg", 4.0)
        self.declare_parameter("publish_period", 0.6)

        self.current_target = [float(value) for value in POSES["ready"]]
        self.last_x = 0.0
        self.last_y = 0.0
        self.visible = False

        self.publisher = self.create_publisher(JointState, "/braccio/joint_command", 10)
        self.status_sub = self.create_subscription(
            String,
            "/braccio/firmware_status",
            self.on_status,
            10,
        )
        self.vision_sub = self.create_subscription(
            String,
            "/braccio/vision_stats",
            self.on_vision,
            10,
        )
        period = float(self.get_parameter("publish_period").value)
        self.timer = self.create_timer(period, self.nudge)

    def on_status(self, msg: String) -> None:
        match = STAT_PATTERN.search(msg.data)
        if not match:
            return
        values = match.group(1).split(",")
        if len(values) == len(JOINT_NAMES):
            self.current_target = [float(value) for value in values]

    def on_vision(self, msg: String) -> None:
        if "visible=true" not in msg.data:
            self.visible = False
            return
        match = VISION_PATTERN.search(msg.data)
        if not match:
            return
        self.visible = True
        self.last_x = float(match.group(1))
        self.last_y = float(match.group(2))

    def bounded_step(self, value: float) -> float:
        max_step = float(self.get_parameter("max_step_deg").value)
        return max(-max_step, min(max_step, value))

    def nudge(self) -> None:
        if not bool(self.get_parameter("enabled").value) or not self.visible:
            return

        deadband = float(self.get_parameter("deadband").value)
        if abs(self.last_x) < deadband and abs(self.last_y) < deadband:
            return

        next_target = list(self.current_target)
        if abs(self.last_x) >= deadband:
            base_gain = float(self.get_parameter("base_gain_deg").value)
            next_target[0] += self.bounded_step(self.last_x * base_gain)
        if abs(self.last_y) >= deadband:
            shoulder_gain = float(self.get_parameter("shoulder_gain_deg").value)
            next_target[1] += self.bounded_step(self.last_y * shoulder_gain)

        next_target = [
            float(clamp_degrees(name, next_target[index]))
            for index, name in enumerate(JOINT_NAMES)
        ]

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = next_target
        self.publisher.publish(msg)
        self.current_target = next_target


def main() -> None:
    rclpy.init()
    node = VisualServoAssist()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
