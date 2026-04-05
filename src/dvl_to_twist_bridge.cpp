#include <algorithm>
#include <array>
#include <string>

#include <dvl_msgs/msg/dvl.hpp>
#include <geometry_msgs/msg/twist_with_covariance_stamped.hpp>
#include <rclcpp/rclcpp.hpp>

class DvlToTwistBridge : public rclcpp::Node
{
public:
  DvlToTwistBridge()
  : Node("dvl_to_twist_bridge")
  {
    input_topic_ = declare_parameter<std::string>("input_topic", "/dvl/data");
    output_topic_ = declare_parameter<std::string>("output_topic", "/dvl/twist");
    output_frame_id_ = declare_parameter<std::string>("output_frame_id", "dvl");
    default_linear_variance_ = declare_parameter<double>("default_linear_variance", 0.02);
    require_valid_velocity_ = declare_parameter<bool>("require_valid_velocity", true);

    const auto sensor_qos = rclcpp::SensorDataQoS();

    publisher_ = create_publisher<geometry_msgs::msg::TwistWithCovarianceStamped>(output_topic_, 10);
    subscription_ = create_subscription<dvl_msgs::msg::DVL>(
      input_topic_, sensor_qos,
      std::bind(&DvlToTwistBridge::handle_msg, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(),
      "Bridging %s -> %s",
      input_topic_.c_str(), output_topic_.c_str());
  }

private:
  void handle_msg(const dvl_msgs::msg::DVL::SharedPtr msg)
  {
    if (require_valid_velocity_ && !msg->velocity_valid) {
      RCLCPP_WARN_THROTTLE(
        get_logger(), *get_clock(), 2000,
        "Skipping DVL sample marked invalid.");
      return;
    }

    geometry_msgs::msg::TwistWithCovarianceStamped out;
    out.header = msg->header;
    if (!output_frame_id_.empty()) {
      out.header.frame_id = output_frame_id_;
    }

    out.twist.twist.linear.x = msg->velocity.x;
    out.twist.twist.linear.y = msg->velocity.y;
    out.twist.twist.linear.z = msg->velocity.z;

    auto & cov = out.twist.covariance;
    cov.fill(0.0);

    if (msg->covariance.size() == 9) {
      for (size_t row = 0; row < 3; ++row) {
        for (size_t col = 0; col < 3; ++col) {
          cov[row * 6 + col] = msg->covariance[row * 3 + col];
        }
      }
    } else if (msg->covariance.size() == 36) {
      std::copy(msg->covariance.begin(), msg->covariance.end(), cov.begin());
    } else {
      cov[0] = default_linear_variance_;
      cov[7] = default_linear_variance_;
      cov[14] = default_linear_variance_;
    }

    publisher_->publish(out);
  }

  std::string input_topic_;
  std::string output_topic_;
  std::string output_frame_id_;
  double default_linear_variance_;
  bool require_valid_velocity_;
  rclcpp::Publisher<geometry_msgs::msg::TwistWithCovarianceStamped>::SharedPtr publisher_;
  rclcpp::Subscription<dvl_msgs::msg::DVL>::SharedPtr subscription_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<DvlToTwistBridge>());
  rclcpp::shutdown();
  return 0;
}
