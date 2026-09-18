import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


def classify_distance(
    distance: float,
    stop_distance: float,
    warning_distance: float,
) -> str:
    if distance <= stop_distance:
        return 'STOP'

    if distance <= warning_distance:
        return 'WARNING'

    return 'CLEAR'


class ObstacleMonitor(Node):

    def __init__(self):
        super().__init__('obstacle_monitor')

        self.declare_parameter('stop_distance', 0.45)
        self.declare_parameter('warning_distance', 0.80)
        self.declare_parameter('front_half_angle_deg', 25.0)

        self.stop_distance = (
            self.get_parameter('stop_distance')
            .get_parameter_value()
            .double_value
        )

        self.warning_distance = (
            self.get_parameter('warning_distance')
            .get_parameter_value()
            .double_value
        )

        self.front_half_angle_deg = (
            self.get_parameter('front_half_angle_deg')
            .get_parameter_value()
            .double_value
        )

        if self.stop_distance <= 0.0:
            raise ValueError('stop_distance must be greater than 0')

        if self.warning_distance <= self.stop_distance:
            raise ValueError(
                'warning_distance must be greater than stop_distance'
            )

        if not 0.0 < self.front_half_angle_deg <= 180.0:
            raise ValueError(
                'front_half_angle_deg must be in range (0, 180]'
            )

        self.scan_subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10,
        )

        self.status_publisher = self.create_publisher(
            String,
            '/amr/obstacle_status',
            10,
        )

        self.last_status = None

        self.get_logger().info(
            'ObstacleMonitor started | '
            f'STOP={self.stop_distance:.2f} m | '
            f'WARNING={self.warning_distance:.2f} m | '
            f'front=±{self.front_half_angle_deg:.1f}°'
        )

    def scan_callback(self, scan: LaserScan) -> None:
        front_ranges = self.extract_front_ranges(scan)

        if not front_ranges:
            self.publish_status('NO_DATA', math.inf)
            return

        min_distance = min(front_ranges)

        status = classify_distance(
            min_distance,
            self.stop_distance,
            self.warning_distance,
        )

        self.publish_status(status, min_distance)

    def extract_front_ranges(self, scan: LaserScan) -> list[float]:
        half_angle = math.radians(self.front_half_angle_deg)
        valid_ranges = []

        for index, distance in enumerate(scan.ranges):
            angle = scan.angle_min + index * scan.angle_increment

            if abs(angle) > half_angle:
                continue

            if not math.isfinite(distance):
                continue

            if not scan.range_min <= distance <= scan.range_max:
                continue

            valid_ranges.append(distance)

        return valid_ranges

    def publish_status(
        self,
        status: str,
        min_distance: float,
    ) -> None:
        message = String()

        if math.isfinite(min_distance):
            message.data = (
                f'{status} | '
                f'min_front_distance={min_distance:.3f} m'
            )
        else:
            message.data = (
                f'{status} | min_front_distance=unknown'
            )

        self.status_publisher.publish(message)

        if status == self.last_status:
            return

        if status == 'STOP':
            self.get_logger().error(message.data)
        elif status == 'WARNING':
            self.get_logger().warning(message.data)
        else:
            self.get_logger().info(message.data)

        self.last_status = status


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleMonitor()

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
