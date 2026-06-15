from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_port = LaunchConfiguration("serial_port")

    return LaunchDescription(
        [
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyACM0"),
            Node(
                package="unoq_braccio_driver",
                executable="serial_bridge",
                name="unoq_braccio_serial_bridge",
                parameters=[{"serial_port": serial_port}],
                output="screen",
            ),
        ]
    )
