"""
On-device pick-and-place using edgeimpulse_ros, meant to run in a Docker
container **on the UNO Q itself** instead of on an external host/VM.

It is the same graph as ``edge_impulse_ros_pick_place.launch.py`` but also
starts the ``tcp_bridge`` so the whole pipeline lives in one container, and the
defaults point at the UNO Q's own App Lab agents over localhost:

* camera MJPEG stream ....... http://127.0.0.1:8080/stream
* arm control agent ......... 127.0.0.1:8765

Run the container with ``network_mode: host`` so these localhost endpoints and
DDS discovery work. Requires ``edgeimpulse_ros`` in the same workspace.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    host = LaunchConfiguration("host")
    port = LaunchConfiguration("port")
    stream_url = LaunchConfiguration("stream_url")
    model_path = LaunchConfiguration("model_path")
    image_topic = LaunchConfiguration("image_topic")
    image_qos = LaunchConfiguration("image_qos")
    confidence_threshold = LaunchConfiguration("confidence_threshold")
    publish_debug_image = LaunchConfiguration("publish_debug_image")
    detections_topic = LaunchConfiguration("detections_topic")
    min_confidence = LaunchConfiguration("min_confidence")
    workflow_file = LaunchConfiguration("workflow_file")

    return LaunchDescription(
        [
            # UNO Q App Lab arm agent, reachable over localhost when the
            # container runs with host networking.
            DeclareLaunchArgument("host", default_value="127.0.0.1"),
            DeclareLaunchArgument("port", default_value="8765"),
            # UNO Q camera MJPEG stream, also over localhost.
            DeclareLaunchArgument(
                "stream_url",
                default_value="http://127.0.0.1:8080/stream",
            ),
            DeclareLaunchArgument(
                "model_path",
                default_value="/models/model.eim",
                description="Path to the aarch64 Edge Impulse .eim model",
            ),
            DeclareLaunchArgument("image_topic", default_value="/braccio/camera/image_raw"),
            DeclareLaunchArgument("image_qos", default_value="sensor_data"),
            DeclareLaunchArgument(
                "confidence_threshold",
                default_value="-1.0",
                description="edgeimpulse_ros publish threshold; <0 uses the model default",
            ),
            DeclareLaunchArgument("publish_debug_image", default_value="false"),
            DeclareLaunchArgument(
                "detections_topic",
                default_value="/edgeimpulse_detector/detections",
            ),
            DeclareLaunchArgument(
                "min_confidence",
                default_value="0.65",
                description="Minimum score for the bridge to publish a label",
            ),
            DeclareLaunchArgument(
                "workflow_file",
                default_value="/config/pick_place_workflows.yaml",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="tcp_bridge",
                name="unoq_braccio_tcp_bridge",
                parameters=[{"host": host, "port": port}],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="mjpeg_camera_node",
                name="unoq_braccio_mjpeg_camera",
                parameters=[{"stream_url": stream_url}],
                output="screen",
            ),
            Node(
                package="edgeimpulse_ros",
                executable="edgeimpulse_detector",
                name="edgeimpulse_detector",
                parameters=[
                    {
                        "model_path": model_path,
                        "image_topic": image_topic,
                        "image_transport": "raw",
                        "image_qos": image_qos,
                        "confidence_threshold": confidence_threshold,
                        "publish_debug_image": publish_debug_image,
                    }
                ],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="detection_label_bridge",
                name="unoq_braccio_detection_label_bridge",
                parameters=[
                    {
                        "detections_topic": detections_topic,
                        "min_confidence": min_confidence,
                    }
                ],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="pick_place_executor",
                name="unoq_braccio_pick_place_executor",
                parameters=[{"workflow_file": workflow_file}],
                output="screen",
            ),
        ]
    )
