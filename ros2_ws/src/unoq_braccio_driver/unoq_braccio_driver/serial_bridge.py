import serial

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

from unoq_braccio_driver.braccio_model import command_line_from_positions


class SerialBridge(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_serial_bridge")
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("command_topic", "/braccio/joint_command")

        port = self.get_parameter("serial_port").value
        baud_rate = self.get_parameter("baud_rate").value
        topic = self.get_parameter("command_topic").value

        self.serial = serial.Serial(port, baud_rate, timeout=1.0)
        self.status_publisher = self.create_publisher(String, "/braccio/firmware_status", 10)
        self.subscription = self.create_subscription(JointState, topic, self.on_command, 10)
        self.get_logger().info(f"Serial bridge connected to {port} at {baud_rate} baud")

    def on_command(self, msg: JointState) -> None:
        if not msg.name or not msg.position:
            self.get_logger().warning("Ignoring empty JointState command")
            return

        line = command_line_from_positions(list(msg.name), list(msg.position))
        self.serial.write((line + "\n").encode("ascii"))
        response = self.serial.readline().decode("ascii", errors="replace").strip()
        if response and response != "OK":
            self.get_logger().warning(f"Firmware response: {response}")
        self.publish_status()

    def publish_status(self) -> None:
        self.serial.write(b"S\n")
        response = self.serial.readline().decode("ascii", errors="replace").strip()
        if response:
            self.status_publisher.publish(String(data=response))

    def destroy_node(self) -> bool:
        if hasattr(self, "serial") and self.serial.is_open:
            self.serial.close()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = SerialBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
