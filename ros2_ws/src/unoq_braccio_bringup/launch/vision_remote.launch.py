from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    stream_url = LaunchConfiguration("stream_url")
    label = LaunchConfiguration("label")

    return LaunchDescription(
        [
            DeclareLaunchArgument("stream_url", default_value="http://unoq.local:8080/stream"),
            DeclareLaunchArgument("label", default_value="object"),
            Node(
                package="unoq_braccio_driver",
                executable="mjpeg_camera_node",
                name="unoq_braccio_mjpeg_camera",
                parameters=[{"stream_url": stream_url}],
                output="screen",
            ),
            Node(
                package="unoq_braccio_driver",
                executable="color_tracker",
                name="unoq_braccio_color_tracker",
                parameters=[{"label": label}],
                output="screen",
            ),
        ]
    )
