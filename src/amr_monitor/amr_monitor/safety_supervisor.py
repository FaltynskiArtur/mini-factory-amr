import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String


class SafetySupervisor(Node):

    def __init__(self):
        super().__init__('safety_supervisor')

        self.stop_active = False

        self.status_subscription = self.create_subscription(
            String,
            '/amr/obstacle_status',
            self.status_callback,
            10,
        )

        self.velocity_subscription = self.create_subscription(
            Twist,
            '/test_cmd_vel',
            self.velocity_callback,
            10,
        )

        self.velocity_publisher = self.create_publisher(
            Twist,
            '/test_cmd_vel_safe',
            10,
        )

        self.get_logger().info(
            'SafetySupervisor started: '
            '/test_cmd_vel -> /test_cmd_vel_safe'
        )

    def status_callback(self, message: String) -> None:
        new_stop_active = message.data.startswith('STOP')

        if new_stop_active == self.stop_active:
            return

        self.stop_active = new_stop_active

        if self.stop_active:
            self.get_logger().warning(
                'SOFTWARE STOP ACTIVE'
            )
            self.publish_stop()
        else:
            self.get_logger().info(
                'Software stop released'
            )

    def velocity_callback(self, command: Twist) -> None:
        if self.stop_active:
            self.publish_stop()
            return

        self.velocity_publisher.publish(command)

    def publish_stop(self) -> None:
        stop_command = Twist()
        self.velocity_publisher.publish(stop_command)


def main(args=None):
    rclpy.init(args=args)

    node = SafetySupervisor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
