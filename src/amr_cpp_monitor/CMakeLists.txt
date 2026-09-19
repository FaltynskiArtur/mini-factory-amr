cmake_minimum_required(VERSION 3.8)
project(amr_cpp_monitor)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(amr_diagnostics src/amr_diagnostics.cpp)

target_compile_features(amr_diagnostics PUBLIC cxx_std_17)

ament_target_dependencies(
  amr_diagnostics
  rclcpp
  sensor_msgs
  std_msgs
)

install(
  TARGETS amr_diagnostics
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
