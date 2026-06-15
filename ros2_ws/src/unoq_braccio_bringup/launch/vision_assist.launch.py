from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    enabled = LaunchConfiguration("enabled")

    return LaunchDescription(
        [
            DeclareLaunchArgument("enabled", default_value="false"),
            Node(
                package="unoq_braccio_driver",
                executable="visual_servo_assist",
                name="unoq_braccio_visual_servo_assist",
                parameters=[{"enabled": enabled}],
                output="screen",
            ),
        ]
    )
