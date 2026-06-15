from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    output_file = LaunchConfiguration("output_file")
    label = LaunchConfiguration("label")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "output_file",
                default_value="edge_impulse/captures/braccio_capture.csv",
            ),
            DeclareLaunchArgument("label", default_value="unlabeled"),
            Node(
                package="unoq_braccio_driver",
                executable="edge_impulse_capture",
                name="unoq_braccio_edge_impulse_capture",
                parameters=[{"output_file": output_file, "label": label}],
                output="screen",
            ),
        ]
    )
