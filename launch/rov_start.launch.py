#!/usr/bin/env python3

import os

from ament_index_python.packages import PackageNotFoundError
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PythonExpression
from launch_ros.actions import Node


def _default_launch_file(package_name: str, relative_path: str) -> str:
    try:
        return os.path.join(get_package_share_directory(package_name), relative_path)
    except PackageNotFoundError:
        return ""


def generate_launch_description() -> LaunchDescription:
    # DVL launch is temporarily disabled.
    # dvl_default = _default_launch_file(
    #     "dvl_a50", os.path.join("launch", "dvl_a50.launch.py")
    # )
    mavros_default = _default_launch_file("mavros", os.path.join("launch", "apm.launch"))

    fcu_url = LaunchConfiguration("fcu_url")
    # dvl_ip = LaunchConfiguration("dvl_ip")
    # use_dvl = LaunchConfiguration("use_dvl")
    # dvl_launch_file = LaunchConfiguration("dvl_launch_file")
    mavros_launch_file = LaunchConfiguration("mavros_launch_file")

    # dvl_enabled = IfCondition(
    #     PythonExpression(["'", use_dvl, "' == 'true' and '", dvl_launch_file, "' != ''"])
    # )
    mavros_enabled = IfCondition(PythonExpression(["'", mavros_launch_file, "' != ''"]))
    dronecan_python_default = os.path.expanduser("~/miniconda3/envs/auv_ros2/bin/python")
    if not os.path.exists(dronecan_python_default):
        dronecan_python_default = "python3"
    dronecan_python = LaunchConfiguration("dronecan_python")

    return LaunchDescription(
        [
            DeclareLaunchArgument("fcu_url", default_value="/dev/ttyACM0:57600"),
            # DeclareLaunchArgument("dvl_ip", default_value="192.168.194.95"),
            # DeclareLaunchArgument("use_dvl", default_value="true"),
            # DeclareLaunchArgument("dvl_launch_file", default_value=dvl_default),
            DeclareLaunchArgument("mavros_launch_file", default_value=mavros_default),
            DeclareLaunchArgument("dronecan_python", default_value=dronecan_python_default),
            # LogInfo(
            #     condition=IfCondition(
            #         PythonExpression(
            #             ["'", use_dvl, "' == 'true' and '", dvl_launch_file, "' == ''"]
            #         )
            #     ),
            #     msg="[rov_start] DVL launch file not found. Skipping DVL include.",
            # ),
            LogInfo(
                condition=IfCondition(PythonExpression(["'", mavros_launch_file, "' == ''"])),
                msg="[rov_start] MAVROS launch file not found. Skipping MAVROS include.",
            ),
            # 1) DVL
            # IncludeLaunchDescription(
            #     AnyLaunchDescriptionSource(dvl_launch_file),
            #     launch_arguments={"ip_address": dvl_ip}.items(),
            #     condition=dvl_enabled,
            # ),
            # 2) MAVROS
            IncludeLaunchDescription(
                AnyLaunchDescriptionSource(mavros_launch_file),
                launch_arguments={"fcu_url": fcu_url}.items(),
                condition=mavros_enabled,
            ),
            # 3) AUV nodes in this package
            Node(
                package="hit25_auv_ros2",
                executable="joy2mavros",
                name="joy2mavros",
                output="screen",
                respawn=True,
            ),
            Node(
                package="hit25_auv_ros2",
                executable="vfr2atm_pressure",
                name="vfr2atm_pressure",
                output="screen",
                respawn=True,
            ),
            Node(
                package="hit25_auv_ros2",
                executable="odom2mavros",
                name="odom2mavros",
                output="screen",
                respawn=True,
            ),
            # 4) DroneCAN battery bridge
            Node(
                package="hit25_auv_ros2",
                executable="dronecan2mavros_battery.py",
                name="dronecan2mavros_battery",
                output="screen",
                respawn=True,
                prefix=dronecan_python,
            ),
        ]
    )
