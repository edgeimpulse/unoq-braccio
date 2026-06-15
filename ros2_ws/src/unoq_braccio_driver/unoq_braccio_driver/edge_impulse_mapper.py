import yaml

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from unoq_braccio_driver.braccio_model import JOINT_NAMES


class EdgeImpulseMapper(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_edge_impulse_mapper")
        self.declare_parameter("mapping_file", "")
        self.declare_parameter("label_topic", "/edge_impulse/label")
        self.mapping = self.load_mapping(self.get_parameter("mapping_file").value)
        self.publisher = self.create_publisher(JointState, "/braccio/joint_command", 10)
        self.subscription = self.create_subscription(
            String,
            self.get_parameter("label_topic").value,
            self.on_label,
            10,
        )

    def load_mapping(self, path: str) -> dict[str, list[float]]:
        if not path:
            self.get_logger().warning("No mapping_file provided")
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data.get("labels", {})

    def on_label(self, msg: String) -> None:
        label = msg.data.strip()
        if label not in self.mapping:
            self.get_logger().warning(f"No Braccio pose mapped for label '{label}'")
            return
        command = JointState()
        command.header.stamp = self.get_clock().now().to_msg()
        command.name = JOINT_NAMES
        command.position = [float(value) for value in self.mapping[label]]
        self.publisher.publish(command)


def main() -> None:
    rclpy.init()
    node = EdgeImpulseMapper()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
