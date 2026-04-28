#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from ament_index_python.packages import PackageNotFoundError
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.actions import SetEnvironmentVariable
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


def _python_supports_modules(python_path: str, modules: tuple[str, ...]) -> bool:
    if not python_path or not os.path.exists(python_path):
        return False
    code = "; ".join(f"import {module}" for module in modules)
    result = subprocess.run(
        [python_path, "-c", code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
        check=False,
    )
    return result.returncode == 0


def _default_dronecan_python() -> str:
    candidates = []

    env_python = os.environ.get("DRONECAN_PYTHON", "").strip()
    if env_python:
        candidates.append(env_python)
    if sys.executable:
        candidates.append(sys.executable)
    python3_path = shutil.which("python3")
    if python3_path:
        candidates.append(python3_path)
    candidates.append("/usr/bin/python3")

    mj311_root = os.environ.get("MJ311_ROOT", os.path.expanduser("~/.venvs/uuv_mujoco"))
    candidates.append(os.path.join(mj311_root, "bin", "python"))

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        candidates.append(os.path.join(conda_prefix, "bin", "python"))

    for candidate in candidates:
        if _python_supports_modules(candidate, ("rclpy", "dronecan")):
            return candidate

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return "python3"


def _default_use_dronecan_battery() -> str:
    # Default to the current ROS Python only. If this env cannot import the
    # required modules, disable the helper rather than silently jumping to a
    # different interpreter and mixing Python ABIs.
    if _python_supports_modules(sys.executable, ("rclpy", "numpy", "sensor_msgs.msg", "dronecan")):
        return "true"
    return "false"


def _macos_library_env() -> dict[str, str]:
    if platform.system() != "Darwin":
        return {}
    conda_prefix = os.environ.get("CONDA_PREFIX", "").strip()
    if not conda_prefix:
        return {}
    conda_lib = os.path.join(conda_prefix, "lib")
    if not os.path.isdir(conda_lib):
        return {}

    env_updates = {}
    for env_name in ("DYLD_FALLBACK_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
        current = os.environ.get(env_name, "").strip()
        paths = [conda_lib]
        if current:
            paths.append(current)
        env_updates[env_name] = ":".join(paths)
    return env_updates


def _workspace_root() -> str:
    launch_path = Path(__file__).resolve()
    for parent in launch_path.parents:
        if (parent / ".geographiclib").is_dir():
            return str(parent)
    return str(launch_path.parents[3])


def _geographiclib_env() -> dict[str, str]:
    geo_root = os.path.join(_workspace_root(), ".geographiclib")
    geoid_path = os.path.join(geo_root, "geoids")

    env_updates = {}
    if os.path.isdir(geo_root):
        env_updates["GEOGRAPHICLIB_DATA"] = geo_root
    if os.path.isdir(geoid_path):
        env_updates["GEOGRAPHICLIB_GEOID_PATH"] = geoid_path
    return env_updates


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
    dronecan_python_default = _default_dronecan_python()
    dronecan_python = LaunchConfiguration("dronecan_python")
    use_dronecan_battery = LaunchConfiguration("use_dronecan_battery")
    use_vfr2atm_pressure = LaunchConfiguration("use_vfr2atm_pressure")
    package_share = get_package_share_directory("hit25_auv_ros2")
    rviz_urdf_path = os.path.join(package_share, "urdf", "rov_rviz_local.urdf")
    with open(rviz_urdf_path, "r", encoding="utf-8") as urdf_file:
        robot_description = urdf_file.read()
    macos_env = _macos_library_env()
    geographiclib_env = _geographiclib_env()
    env_actions = [
        SetEnvironmentVariable(name=name, value=value)
        for name, value in {**macos_env, **geographiclib_env}.items()
    ]

    return LaunchDescription(
        env_actions
        + [
            DeclareLaunchArgument("fcu_url", default_value="/dev/ttyACM0:57600"),
            # DeclareLaunchArgument("dvl_ip", default_value="192.168.194.95"),
            # DeclareLaunchArgument("use_dvl", default_value="true"),
            # DeclareLaunchArgument("dvl_launch_file", default_value=dvl_default),
            DeclareLaunchArgument("mavros_launch_file", default_value=mavros_default),
            DeclareLaunchArgument("dronecan_python", default_value=dronecan_python_default),
            DeclareLaunchArgument(
                "use_dronecan_battery", default_value=_default_use_dronecan_battery()
            ),
            DeclareLaunchArgument(
                "use_vfr2atm_pressure",
                default_value="false",
            ),
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
                condition=IfCondition(use_vfr2atm_pressure),
            ),
            Node(
                package="hit25_auv_ros2",
                executable="odom2mavros",
                name="odom2mavros",
                output="screen",
                respawn=True,
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            # 4) DroneCAN battery bridge
            Node(
                package="hit25_auv_ros2",
                executable="dronecan2mavros_battery.py",
                name="dronecan2mavros_battery",
                output="screen",
                respawn=True,
                prefix=dronecan_python,
                condition=IfCondition(use_dronecan_battery),
            ),
        ]
    )
