// Copyright 2026 Artur Faltynski
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/string.hpp"

class AmrDiagnostics : public rclcpp::Node
{
public:
  AmrDiagnostics()
  : Node("amr_cpp_diagnostics")
  {
    stop_distance_ = declare_parameter<double>("stop_distance", 0.35);
    warning_distance_ = declare_parameter<double>("warning_distance", 0.70);
    front_half_angle_deg_ = declare_parameter<double>("front_half_angle_deg", 20.0);

    status_publisher_ = create_publisher<std_msgs::msg::String>(
      "/amr/cpp_obstacle_status",
      10);

    scan_subscription_ = create_subscription<sensor_msgs::msg::LaserScan>(
      "/scan",
      rclcpp::SensorDataQoS(),
      std::bind(&AmrDiagnostics::scan_callback, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(),
      "C++ AMR diagnostics started: stop=%.2f m, warning=%.2f m, sector=+/-%.1f deg",
      stop_distance_,
      warning_distance_,
      front_half_angle_deg_);
  }

private:
  void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg)
  {
    const double half_angle_rad =
      front_half_angle_deg_ * std::acos(-1.0) / 180.0;

    std::vector<float> valid_front_ranges;
    valid_front_ranges.reserve(msg->ranges.size());

    for (std::size_t index = 0; index < msg->ranges.size(); ++index) {
      const double angle =
        static_cast<double>(msg->angle_min) +
        static_cast<double>(index) * static_cast<double>(msg->angle_increment);

      if (std::abs(angle) > half_angle_rad) {
        continue;
      }

      const float range = msg->ranges[index];

      if (!std::isfinite(range)) {
        continue;
      }

      if (range < msg->range_min || range > msg->range_max) {
        continue;
      }

      valid_front_ranges.push_back(range);
    }

    if (valid_front_ranges.empty()) {
      publish_status("NO_DATA", std::numeric_limits<double>::quiet_NaN());
      return;
    }

    const double minimum_distance =
      static_cast<double>(
      *std::min_element(valid_front_ranges.begin(), valid_front_ranges.end()));

    std::string state;

    if (minimum_distance <= stop_distance_) {
      state = "STOP";
    } else if (minimum_distance <= warning_distance_) {
      state = "WARNING";
    } else {
      state = "CLEAR";
    }

    publish_status(state, minimum_distance);
  }

  void publish_status(const std::string & state, const double distance)
  {
    std_msgs::msg::String message;

    if (std::isfinite(distance)) {
      message.data =
        state + " min_distance=" + std::to_string(distance);
    } else {
      message.data = state + " min_distance=nan";
    }

    status_publisher_->publish(message);

    RCLCPP_INFO_THROTTLE(
      get_logger(),
      *get_clock(),
      2000,
      "%s",
      message.data.c_str());
  }

  double stop_distance_;
  double warning_distance_;
  double front_half_angle_deg_;

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_publisher_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<AmrDiagnostics>();
  rclcpp::spin(node);

  rclcpp::shutdown();
  return 0;
}
