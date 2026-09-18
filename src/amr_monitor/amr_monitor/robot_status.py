import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotStatusNode(Node):

    def __init__(self):
        super().__init__('robot_status')

        self.publisher = self.create_publisher(
            String,
            '/amr/status',
            10,
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_status,
        )

        self.counter = 0

        self.get_logger().info(
            'AMR Robot Status node started'
        )

    def publish_status(self):
        message = String()

        message.data = (
            f'AMR_01 ONLINE | heartbeat={self.counter}'
        )

        self.publisher.publish(message)

        self.get_logger().info(
            f'Published: "{message.data}"'
        )

        self.counter += 1


def main(args=None):
    rclpy.init(args=args)

    node = RobotStatusNode()

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
