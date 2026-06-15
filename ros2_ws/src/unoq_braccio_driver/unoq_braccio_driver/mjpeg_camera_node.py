import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class MjpegCameraNode(Node):
    def __init__(self) -> None:
        super().__init__("unoq_braccio_mjpeg_camera")
        self.declare_parameter("stream_url", "http://unoq.local:8080/stream")
        self.declare_parameter("frame_id", "unoq_usb_camera")
        self.declare_parameter("fps", 10.0)

        self.stream_url = str(self.get_parameter("stream_url").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        fps = float(self.get_parameter("fps").value)

        self.capture = cv2.VideoCapture(self.stream_url)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open MJPEG stream {self.stream_url}")

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, "/braccio/camera/image_raw", 10)
        self.timer = self.create_timer(1.0 / max(fps, 1.0), self.publish_frame)
        self.get_logger().info(f"MJPEG camera publishing from {self.stream_url}")

    def publish_frame(self) -> None:
        ok, frame = self.capture.read()
        if not ok:
            self.get_logger().warning("MJPEG frame read failed; reconnecting")
            self.capture.release()
            self.capture = cv2.VideoCapture(self.stream_url)
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        self.publisher.publish(msg)

    def destroy_node(self) -> bool:
        if hasattr(self, "capture"):
            self.capture.release()
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = MjpegCameraNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
