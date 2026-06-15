import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from unoq_braccio_driver.braccio_model import JOINT_NAMES, POSES


class PoseDemo(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_pose_demo")
        self.declare_parameter("pose", "ready")
        self.publisher = self.create_publisher(JointState, "/braccio/joint_command", 10)
        self.timer = self.create_timer(0.5, self.publish_once)
        self.sent = False

    def publish_once(self) -> None:
        if self.sent:
            rclpy.shutdown()
            return

        pose_name = self.get_parameter("pose").value
        if pose_name not in POSES:
            self.get_logger().error(f"Unknown pose '{pose_name}'. Available: {', '.join(POSES)}")
            rclpy.shutdown()
            return

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = JOINT_NAMES
        msg.position = [float(value) for value in POSES[pose_name]]
        self.publisher.publish(msg)
        self.get_logger().info(f"Published pose: {pose_name}")
        self.sent = True


def main() -> None:
    rclpy.init()
    node = PoseDemo()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
