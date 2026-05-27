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
from launch_ros.parameter_descriptions import ParameterValue


def _default_launch_file(package_name: str, relative_path: str) -> str:
    try:
        return os.path.join(get_package_share_directory(package_name), relative_path)
    except PackageNotFoundError:
        return ""


def _static_tf_node(name, parent_frame, child_frame, x, y, z, roll, pitch, yaw) -> Node:
    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name=name,
        output="screen",
        arguments=[
            "--x", x,
            "--y", y,
            "--z", z,
            "--roll", roll,
            "--pitch", pitch,
            "--yaw", yaw,
            "--frame-id", parent_frame,
            "--child-frame-id", child_frame,
        ],
    )


def generate_launch_description() -> LaunchDescription:
    dvl_default = _default_launch_file(
        "dvl_a50", os.path.join("launch", "dvl_a50.launch.py")
    )
    mavros_default = _default_launch_file("mavros", os.path.join("launch", "apm.launch"))
    localization_default = os.path.join(
        get_package_share_directory("hit25_auv_ros2"), "config", "auv_ekf.yaml")
    dronecan_python_default = os.path.expanduser("~/miniconda3/envs/auv_ros2/bin/python")
    if not os.path.exists(dronecan_python_default):
        dronecan_python_default = "python3"

    launch_arguments = [
        # Core connections
        DeclareLaunchArgument("fcu_url", default_value="/dev/ttyACM0:57600"),
        DeclareLaunchArgument("mavros_launch_file", default_value=mavros_default),
        DeclareLaunchArgument("dronecan_python", default_value=dronecan_python_default),
        DeclareLaunchArgument("use_external_baro_bridge", default_value="false"),
        DeclareLaunchArgument(
            "external_baro_connection_url",
            default_value="udpin:0.0.0.0:14500",
        ),
        # Frames
        DeclareLaunchArgument("base_frame", default_value="base_link"),
        DeclareLaunchArgument("fcu_frame", default_value="fcu_link"),
        DeclareLaunchArgument("dvl_frame", default_value="dvl"),
        DeclareLaunchArgument("depth_frame", default_value="depth_link"),
        DeclareLaunchArgument("imu_frame", default_value="imu_link"),
        # base_link -> fcu_link (FCU/IMU) static TF
        DeclareLaunchArgument("base_to_fcu_x", default_value="0.11"),
        DeclareLaunchArgument("base_to_fcu_y", default_value="-0.00034"),
        DeclareLaunchArgument("base_to_fcu_z", default_value="0.092"),
        DeclareLaunchArgument("base_to_fcu_roll", default_value="0.0"),
        DeclareLaunchArgument("base_to_fcu_pitch", default_value="0.0"),
        DeclareLaunchArgument("base_to_fcu_yaw", default_value="0.0"),
        # base_link -> DVL static TF
        DeclareLaunchArgument("dvl_x", default_value="-0.03196"),
        DeclareLaunchArgument("dvl_y", default_value="0.0"),
        DeclareLaunchArgument("dvl_z", default_value="-0.097"),
        DeclareLaunchArgument("dvl_roll", default_value="0.0"),
        DeclareLaunchArgument("dvl_pitch", default_value="0.0"),
        DeclareLaunchArgument("dvl_yaw", default_value="0.0"),
        # base_link -> depth static TF
        DeclareLaunchArgument("depth_x", default_value="-0.17364"),
        DeclareLaunchArgument("depth_y", default_value="-0.03034"),
        DeclareLaunchArgument("depth_z", default_value="0.0536"),
        DeclareLaunchArgument("depth_roll", default_value="0.0"),
        DeclareLaunchArgument("depth_pitch", default_value="0.0"),
        DeclareLaunchArgument("depth_yaw", default_value="0.0"),
        # fcu_link -> imu_link static TF
        DeclareLaunchArgument("imu_x", default_value="0.0"),
        DeclareLaunchArgument("imu_y", default_value="0.0"),
        DeclareLaunchArgument("imu_z", default_value="0.0"),
        DeclareLaunchArgument("imu_roll", default_value="0.0"),
        DeclareLaunchArgument("imu_pitch", default_value="0.0"),
        DeclareLaunchArgument("imu_yaw", default_value="0.0"),
        DeclareLaunchArgument("dvl_ip", default_value="192.168.194.95"),
        DeclareLaunchArgument("use_dvl", default_value="true"),
        DeclareLaunchArgument("dvl_launch_file", default_value=dvl_default),
        DeclareLaunchArgument("use_localization", default_value="true"),
        DeclareLaunchArgument("localization_params_file", default_value=localization_default),
        DeclareLaunchArgument("pressure_topic", default_value="/mavros/imu/static_pressure"),
        DeclareLaunchArgument("pressure_input_mode", default_value="pressure_pa"),
        DeclareLaunchArgument("fluid_density", default_value="1000.0"),
    ]

    fcu_url = LaunchConfiguration("fcu_url")
    dvl_ip = LaunchConfiguration("dvl_ip")
    use_dvl = LaunchConfiguration("use_dvl")
    dvl_launch_file = LaunchConfiguration("dvl_launch_file")
    use_localization = LaunchConfiguration("use_localization")
    localization_params_file = LaunchConfiguration("localization_params_file")
    pressure_topic = LaunchConfiguration("pressure_topic")
    pressure_input_mode = LaunchConfiguration("pressure_input_mode")
    fluid_density = LaunchConfiguration("fluid_density")
    mavros_launch_file = LaunchConfiguration("mavros_launch_file")
    dronecan_python = LaunchConfiguration("dronecan_python")
    use_external_baro_bridge = LaunchConfiguration("use_external_baro_bridge")
    external_baro_connection_url = LaunchConfiguration("external_baro_connection_url")

    base_frame = LaunchConfiguration("base_frame")
    fcu_frame = LaunchConfiguration("fcu_frame")
    dvl_frame = LaunchConfiguration("dvl_frame")
    depth_frame = LaunchConfiguration("depth_frame")
    imu_frame = LaunchConfiguration("imu_frame")

    base_to_fcu_x = LaunchConfiguration("base_to_fcu_x")
    base_to_fcu_y = LaunchConfiguration("base_to_fcu_y")
    base_to_fcu_z = LaunchConfiguration("base_to_fcu_z")
    base_to_fcu_roll = LaunchConfiguration("base_to_fcu_roll")
    base_to_fcu_pitch = LaunchConfiguration("base_to_fcu_pitch")
    base_to_fcu_yaw = LaunchConfiguration("base_to_fcu_yaw")

    dvl_x = LaunchConfiguration("dvl_x")
    dvl_y = LaunchConfiguration("dvl_y")
    dvl_z = LaunchConfiguration("dvl_z")
    dvl_roll = LaunchConfiguration("dvl_roll")
    dvl_pitch = LaunchConfiguration("dvl_pitch")
    dvl_yaw = LaunchConfiguration("dvl_yaw")

    depth_x = LaunchConfiguration("depth_x")
    depth_y = LaunchConfiguration("depth_y")
    depth_z = LaunchConfiguration("depth_z")
    depth_roll = LaunchConfiguration("depth_roll")
    depth_pitch = LaunchConfiguration("depth_pitch")
    depth_yaw = LaunchConfiguration("depth_yaw")

    imu_x = LaunchConfiguration("imu_x")
    imu_y = LaunchConfiguration("imu_y")
    imu_z = LaunchConfiguration("imu_z")
    imu_roll = LaunchConfiguration("imu_roll")
    imu_pitch = LaunchConfiguration("imu_pitch")
    imu_yaw = LaunchConfiguration("imu_yaw")

    dvl_enabled = IfCondition(
        PythonExpression(["'", use_dvl, "' == 'true' and '", dvl_launch_file, "' != ''"]))
    localization_enabled = IfCondition(PythonExpression(["'", use_localization, "' == 'true'"]))
    mavros_enabled = IfCondition(PythonExpression(["'", mavros_launch_file, "' != ''"]))

    launch_actions = [
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
        LogInfo(
            condition=IfCondition(
                PythonExpression(["'", use_dvl, "' == 'true' and '", dvl_launch_file, "' == ''"])
            ),
            msg="[rov_start] DVL launch file not found. Skipping DVL include.",
        ),
        # 1) DVL
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(dvl_launch_file),
            launch_arguments={
                "ip_address": dvl_ip,
                "velocity_frame_id": dvl_frame,
                "position_frame_id": dvl_frame,
            }.items(),
            condition=dvl_enabled,
        ),
        # 2) MAVROS
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(mavros_launch_file),
            launch_arguments={"fcu_url": fcu_url}.items(),
            condition=mavros_enabled,
        ),
        # 3) Vehicle and sensor static TFs
        _static_tf_node(
            "base_to_fcu_static_tf",
            base_frame,
            fcu_frame,
            base_to_fcu_x,
            base_to_fcu_y,
            base_to_fcu_z,
            base_to_fcu_roll,
            base_to_fcu_pitch,
            base_to_fcu_yaw,
        ),
        _static_tf_node(
            "dvl_static_tf",
            base_frame,
            dvl_frame,
            dvl_x,
            dvl_y,
            dvl_z,
            dvl_roll,
            dvl_pitch,
            dvl_yaw,
        ),
        _static_tf_node(
            "depth_static_tf",
            base_frame,
            depth_frame,
            depth_x,
            depth_y,
            depth_z,
            depth_roll,
            depth_pitch,
            depth_yaw,
        ),
        _static_tf_node(
            "imu_static_tf",
            fcu_frame,
            imu_frame,
            imu_x,
            imu_y,
            imu_z,
            imu_roll,
            imu_pitch,
            imu_yaw,
        ),
        # 4) AUV nodes in this package
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
            parameters=[{"frame_id": depth_frame}],
        ),
        Node(
            package="hit25_auv_ros2",
            executable="dvl_to_twist_bridge",
            name="dvl_to_twist_bridge",
            output="screen",
            respawn=True,
            parameters=[{"output_frame_id": dvl_frame}],
            condition=localization_enabled,
        ),
        Node(
            package="hit25_auv_ros2",
            executable="pressure_to_depth_pose",
            name="pressure_to_depth_pose",
            output="screen",
            respawn=True,
            parameters=[
                {"input_topic": pressure_topic},
                {"input_mode": pressure_input_mode},
                {"world_frame": "odom"},
                {"fluid_density": ParameterValue(fluid_density, value_type=float)},
            ],
            condition=localization_enabled,
        ),
        Node(
            package="robot_localization",
            executable="ekf_node",
            name="ekf_filter_node",
            output="screen",
            respawn=True,
            parameters=[localization_params_file],
            condition=localization_enabled,
        ),
        Node(
            package="hit25_auv_ros2",
            executable="odom2mavros",
            name="odom2mavros",
            output="screen",
            respawn=True,
        ),
        # 5) DroneCAN battery bridge
        Node(
            package="hit25_auv_ros2",
            executable="dronecan2mavros_battery_v2.py",
            name="dronecan2mavros_battery",
            output="screen",
            respawn=True,
            prefix=dronecan_python,
        ),
    ]

    return LaunchDescription(launch_arguments + launch_actions)
