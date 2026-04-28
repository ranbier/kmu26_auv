cmake_minimum_required(VERSION 3.8)
project(hit25_auv_ros2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

if(APPLE)
  set(CMAKE_MACOSX_RPATH ON)
  set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

  set(_hit25_runtime_rpaths "@loader_path/..")
  if(DEFINED ENV{CONDA_PREFIX} AND EXISTS "$ENV{CONDA_PREFIX}/lib")
    list(APPEND _hit25_runtime_rpaths "$ENV{CONDA_PREFIX}/lib")
  endif()
  foreach(_prefix ${CMAKE_PREFIX_PATH})
    if(EXISTS "${_prefix}/lib")
      list(APPEND _hit25_runtime_rpaths "${_prefix}/lib")
    endif()
  endforeach()
  list(REMOVE_DUPLICATES _hit25_runtime_rpaths)

  function(hit25_apply_macos_rpath target_name)
    set_target_properties(
      ${target_name}
      PROPERTIES
        BUILD_RPATH "${_hit25_runtime_rpaths}"
        INSTALL_RPATH "${_hit25_runtime_rpaths}"
    )
  endfunction()

  if(DEFINED ENV{CONDA_PREFIX} AND EXISTS "$ENV{CONDA_PREFIX}/bin/python3")
    set(Python3_FIND_VIRTUALENV FIRST CACHE STRING "" FORCE)
    set(Python3_ROOT_DIR "$ENV{CONDA_PREFIX}" CACHE PATH "" FORCE)
    set(Python3_EXECUTABLE "$ENV{CONDA_PREFIX}/bin/python3" CACHE FILEPATH "" FORCE)

    if(EXISTS "$ENV{CONDA_PREFIX}/include/python3.11")
      set(Python3_INCLUDE_DIR "$ENV{CONDA_PREFIX}/include/python3.11" CACHE PATH "" FORCE)
    endif()

    if(EXISTS "$ENV{CONDA_PREFIX}/lib/libpython3.11.dylib")
      set(Python3_LIBRARY "$ENV{CONDA_PREFIX}/lib/libpython3.11.dylib" CACHE FILEPATH "" FORCE)
      set(Python3_LIBRARY_RELEASE "$ENV{CONDA_PREFIX}/lib/libpython3.11.dylib" CACHE FILEPATH "" FORCE)
    endif()
  endif()
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
if(APPLE)
  find_package(Python3 COMPONENTS Development REQUIRED)
endif()
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
if(APPLE)
  target_link_libraries(cam2baselink_static_tf Python3::Python)
  hit25_apply_macos_rpath(cam2baselink_static_tf)
endif()

add_executable(joy2mavros src/joy2mavros.cpp)
ament_target_dependencies(joy2mavros rclcpp sensor_msgs mavros_msgs)
if(APPLE)
  target_link_libraries(joy2mavros Python3::Python)
  hit25_apply_macos_rpath(joy2mavros)
endif()

add_executable(odom2mavros src/odom2mavros.cpp)
ament_target_dependencies(odom2mavros rclcpp nav_msgs geometry_msgs tf2 tf2_geometry_msgs)
if(APPLE)
  target_link_libraries(odom2mavros Python3::Python)
  hit25_apply_macos_rpath(odom2mavros)
endif()

add_executable(vfr2atm_pressure src/vfr2atm_pressure.cpp)
ament_target_dependencies(vfr2atm_pressure rclcpp mavros_msgs sensor_msgs)
if(APPLE)
  target_link_libraries(vfr2atm_pressure Python3::Python)
  hit25_apply_macos_rpath(vfr2atm_pressure)
endif()

add_executable(guided_control src/guided_control.cpp)
ament_target_dependencies(guided_control rclcpp geometry_msgs tf2 mavros_msgs)
if(APPLE)
  target_link_libraries(guided_control Python3::Python)
  hit25_apply_macos_rpath(guided_control)
endif()

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
  rviz
  urdf
  meshes
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
