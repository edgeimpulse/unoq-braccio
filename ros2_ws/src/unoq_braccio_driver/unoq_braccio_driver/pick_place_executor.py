import time

import rclpy
import yaml
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from unoq_braccio_driver.braccio_model import JOINT_NAMES


class PickPlaceExecutor(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_pick_place_executor")
        self.declare_parameter("workflow_file", "edge_impulse/pick_place_workflows.yaml")
        self.declare_parameter("label_topic", "/edge_impulse/label")
        self.declare_parameter("step_delay", 1.2)
        self.declare_parameter("enabled", True)

        self.workflows = self.load_workflows(str(self.get_parameter("workflow_file").value))
        self.publisher = self.create_publisher(JointState, "/braccio/joint_command", 10)
        self.subscription = self.create_subscription(
            String,
            str(self.get_parameter("label_topic").value),
            self.on_label,
            10,
        )
        self.busy = False

    def load_workflows(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data.get("items", {})

    def on_label(self, msg: String) -> None:
        if not bool(self.get_parameter("enabled").value):
            return
        label = msg.data.strip()
        if self.busy:
            self.get_logger().info(f"Ignoring '{label}' while sequence is running")
            return
        if label not in self.workflows:
            self.get_logger().warning(f"No pick/place workflow mapped for '{label}'")
            return

        self.busy = True
        try:
            self.run_sequence(label, self.workflows[label].get("sequence", []))
        finally:
            self.busy = False

    def run_sequence(self, label: str, sequence: list[dict]) -> None:
        delay = float(self.get_parameter("step_delay").value)
        self.get_logger().info(f"Running pick/place workflow for {label}")
        for step in sequence:
            pose = step.get("pose")
            wait = float(step.get("wait", delay))
            if not pose or len(pose) != len(JOINT_NAMES):
                self.get_logger().warning(f"Skipping invalid step for {label}: {step}")
                continue
            command = JointState()
            command.header.stamp = self.get_clock().now().to_msg()
            command.name = JOINT_NAMES
            command.position = [float(value) for value in pose]
            self.publisher.publish(command)
            time.sleep(wait)


def main() -> None:
    rclpy.init()
    node = PickPlaceExecutor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
