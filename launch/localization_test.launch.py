#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_prefix
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.actions import RegisterEventHandler
from launch.actions import TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("hit25_auv_ros2")
    package_prefix = get_package_prefix("hit25_auv_ros2")
    rov_launch_file = os.path.join(package_share, "launch", "rov_start.launch.py")
    dvl_setup_script = os.path.join(package_prefix, "lib", "hit25_auv_ros2", "dvl_setup.sh")

    setup_delay = LaunchConfiguration("setup_delay")
    dvl_setup_topic = LaunchConfiguration("dvl_setup_topic")
    odom_topic = LaunchConfiguration("odom_topic")
    path_topic = LaunchConfiguration("path_topic")
    path_frame = LaunchConfiguration("path_frame")
    base_frame = LaunchConfiguration("base_frame")
    min_translation = LaunchConfiguration("min_translation")
    max_poses = LaunchConfiguration("max_poses")

    rov_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rov_launch_file),
    )

    dvl_setup_process = ExecuteProcess(
        cmd=[dvl_setup_script, dvl_setup_topic],
        output="screen",
    )

    localization_debug_node = Node(
        package="hit25_auv_ros2",
        executable="localization_debug",
        name="localization_debug_node",
        output="screen",
        parameters=[
            {
                "odom_topic": odom_topic,
                "path_topic": path_topic,
                "path_frame": path_frame,
                "base_frame": base_frame,
                "min_translation": min_translation,
                "max_poses": max_poses,
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("setup_delay", default_value="5.0"),
            DeclareLaunchArgument("dvl_setup_topic", default_value="/dvl/config/command"),
            DeclareLaunchArgument("odom_topic", default_value="/odometry/filtered"),
            DeclareLaunchArgument("path_topic", default_value="/localization/path"),
            DeclareLaunchArgument("path_frame", default_value="odom"),
            DeclareLaunchArgument("base_frame", default_value="base_link"),
            DeclareLaunchArgument("min_translation", default_value="0.0"),
            DeclareLaunchArgument("max_poses", default_value="5000"),
            LogInfo(
                msg=[
                    "[localization_test] Starting rov_start. Waiting ",
                    setup_delay,
                    " seconds before DVL setup.",
                ]
            ),
            rov_launch,
            TimerAction(
                period=setup_delay,
                actions=[
                    LogInfo(
                        msg=[
                            "[localization_test] Running dvl_setup.sh on ",
                            dvl_setup_topic,
                        ]
                    ),
                    dvl_setup_process,
                ],
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=dvl_setup_process,
                    on_exit=[
                        LogInfo(
                            msg=(
                                "[localization_test] dvl_setup.sh finished. "
                                "Starting localization_debug."
                            )
                        ),
                        localization_debug_node,
                    ],
                )
            ),
        ]
    )
