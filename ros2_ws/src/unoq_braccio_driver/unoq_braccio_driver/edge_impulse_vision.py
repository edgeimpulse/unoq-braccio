import json
import os
import shlex
import subprocess
import tempfile
import time

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class EdgeImpulseVision(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_edge_impulse_vision")
        self.declare_parameter("image_topic", "/braccio/camera/image_raw")
        self.declare_parameter("runner_command", "")
        self.declare_parameter("min_confidence", 0.65)
        self.declare_parameter("max_fps", 2.0)
        self.declare_parameter("publish_unmatched", False)

        self.bridge = CvBridge()
        self.last_run = 0.0
        self.min_confidence = float(self.get_parameter("min_confidence").value)
        self.max_period = 1.0 / max(float(self.get_parameter("max_fps").value), 0.1)
        self.runner_command = str(self.get_parameter("runner_command").value)
        self.publish_unmatched = bool(self.get_parameter("publish_unmatched").value)

        self.label_pub = self.create_publisher(String, "/edge_impulse/label", 10)
        self.detection_pub = self.create_publisher(String, "/edge_impulse/detection", 10)
        self.subscription = self.create_subscription(
            Image,
            str(self.get_parameter("image_topic").value),
            self.on_image,
            10,
        )

        if not self.runner_command:
            self.get_logger().warning("No runner_command configured; vision inference is disabled")

    def on_image(self, msg: Image) -> None:
        if not self.runner_command:
            return
        now = time.monotonic()
        if now - self.last_run < self.max_period:
            return
        self.last_run = now

        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            image_path = handle.name
        try:
            cv2.imwrite(image_path, frame)
            result = self.run_inference(image_path)
        finally:
            try:
                os.remove(image_path)
            except OSError:
                pass

        if not result:
            return

        self.detection_pub.publish(String(data=json.dumps(result)))
        label = str(result.get("label", "")).strip()
        confidence = float(result.get("confidence", 0.0))
        if label and confidence >= self.min_confidence:
            self.label_pub.publish(String(data=label))
        elif self.publish_unmatched:
            self.label_pub.publish(String(data="unmatched"))

    def run_inference(self, image_path: str) -> dict | None:
        command = self.runner_command.format(image=shlex.quote(image_path))
        try:
            completed = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                timeout=15.0,
            )
        except subprocess.SubprocessError as error:
            self.get_logger().warning(f"Edge Impulse runner failed: {error}")
            return None

        output = completed.stdout.strip().splitlines()
        if not output:
            return None
        try:
            return json.loads(output[-1])
        except json.JSONDecodeError as error:
            self.get_logger().warning(f"Runner did not emit JSON: {error}")
            return None


def main() -> None:
    rclpy.init()
    node = EdgeImpulseVision()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
