import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

SIM_JOINT_NAMES = ["base", "shoulder", "elbow", "wrist_vertical"]


class JointStateSimulator(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_joint_state_simulator")
        self.publisher = self.create_publisher(JointState, "/joint_states", 10)
        self.subscription = self.create_subscription(
            JointState,
            "/braccio/joint_command",
            self.on_command,
            10,
        )

    def on_command(self, msg: JointState) -> None:
        values_by_name = dict(zip(msg.name, msg.position))
        state = JointState()
        state.header.stamp = self.get_clock().now().to_msg()
        state.name = SIM_JOINT_NAMES
        state.position = [
            math.radians(float(values_by_name.get(name, 90.0)) - 90.0)
            for name in SIM_JOINT_NAMES
        ]
        self.publisher.publish(state)


def main() -> None:
    rclpy.init()
    node = JointStateSimulator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
