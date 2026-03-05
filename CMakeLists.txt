cmake_minimum_required(VERSION 3.8)
project(hit25_auv_ros2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(mavros_msgs REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

add_executable(cam2baselink_static_tf src/cam2baselink_static_tf.cpp)
ament_target_dependencies(cam2baselink_static_tf rclcpp geometry_msgs tf2 tf2_ros)

add_executable(joy2mavros src/joy2mavros.cpp)
ament_target_dependencies(joy2mavros rclcpp sensor_msgs mavros_msgs)

add_executable(odom2mavros src/odom2mavros.cpp)
ament_target_dependencies(odom2mavros rclcpp nav_msgs geometry_msgs tf2 tf2_geometry_msgs)

add_executable(vfr2atm_pressure src/vfr2atm_pressure.cpp)
ament_target_dependencies(vfr2atm_pressure rclcpp mavros_msgs sensor_msgs)

add_executable(guided_control src/guided_control.cpp)
ament_target_dependencies(guided_control rclcpp geometry_msgs tf2 mavros_msgs)

install(TARGETS
  cam2baselink_static_tf
  joy2mavros
  odom2mavros
  vfr2atm_pressure
  guided_control
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/dronecan2mavros_battery.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
