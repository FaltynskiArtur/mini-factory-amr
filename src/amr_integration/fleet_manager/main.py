import math
import time
from typing import Any

import httpx
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import (
    BasicNavigator,
    TaskResult,
)

from src.amr_integration.mqtt.telemetry import TelemetryPublisher
from src.amr_integration.opcua.station_gateway import (
    OpcUaStationClient,
)


WMS_URL = "http://127.0.0.1:8000"
POLL_INTERVAL_SECONDS = 2.0


STATIONS = {
    "WAREHOUSE_A": (0.5, 0.5, 0.0),
    "ASSEMBLY_LINE_01": (2.0, 1.0, 0.0),
    "A": (0.5, 0.5, 0.0),
    "B": (1.0, 0.5, 0.0),
    "C": (1.0, 1.0, 0.0),
    "D": (1.5, 1.0, 0.0),
    "E": (1.5, 1.5, 0.0),
    "F": (2.0, 1.5, 0.0),
}


class FleetManager:
    def __init__(
        self,
        wms_url: str,
        navigator: BasicNavigator,
        telemetry: TelemetryPublisher,
        station: OpcUaStationClient,
    ) -> None:
        self.wms_url = wms_url
        self.navigator = navigator
        self.telemetry = telemetry
        self.station = station

        self.client = httpx.Client(
            base_url=wms_url,
            timeout=5.0,
        )

    def get_missions(self) -> list[dict[str, Any]]:
        response = self.client.get("/missions")
        response.raise_for_status()
        return response.json()

    def update_status(
        self,
        mission_id: str,
        status: str,
    ) -> None:
        response = self.client.patch(
            f"/missions/{mission_id}/status",
            json={
                "status": status,
            },
        )
        response.raise_for_status()

    def publish_telemetry(
        self,
        mission: dict[str, Any],
        robot_status: str,
    ) -> None:
        try:
            self.telemetry.publish_robot_status(
                robot_id=mission["robot_id"],
                status=robot_status,
                mission_id=mission["mission_id"],
            )

            print(
                f"MQTT -> {mission['robot_id']}: "
                f"{robot_status}"
            )

        except Exception as error:
            print(
                f"MQTT telemetry error: {error}"
            )

    def check_station_available(
        self,
    ) -> bool:
        try:
            state = self.station.read_state()

            print()
            print("OPC UA station state:")
            print(
                f"  StationReady:  "
                f"{state.station_ready}"
            )
            print(
                f"  EmergencyStop: "
                f"{state.emergency_stop}"
            )
            print(
                f"  RobotPresent:  "
                f"{state.robot_present}"
            )
            print(
                f"  MissionActive: "
                f"{state.mission_active}"
            )
            print(
                f"  RobotId:       "
                f"{state.robot_id!r}"
            )

            if state.emergency_stop:
                print(
                    "Station unavailable: "
                    "EmergencyStop is active"
                )
                return False

            if not state.station_ready:
                print(
                    "Station unavailable: "
                    "StationReady is False"
                )
                return False

            if state.robot_present:
                print(
                    "Station unavailable: "
                    "another robot is present"
                )
                return False

            if state.mission_active:
                print(
                    "Station unavailable: "
                    "another mission is active"
                )
                return False

            print(
                "Station available for mission"
            )
            return True

        except Exception as error:
            print(
                "OPC UA communication error: "
                f"{error}"
            )
            return False

    def occupy_station(
        self,
        robot_id: str,
    ) -> None:
        self.station.set_robot_state(
            robot_id=robot_id,
            robot_present=True,
            mission_active=True,
        )

        print(
            "OPC UA -> station occupied by "
            f"{robot_id}"
        )

    def release_station(
        self,
    ) -> None:
        self.station.set_robot_state(
            robot_id="",
            robot_present=False,
            mission_active=False,
        )

        print(
            "OPC UA -> station released"
        )

    def find_next_mission(
        self,
        missions: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        queued_missions = [
            mission
            for mission in missions
            if mission["status"] == "QUEUED"
        ]

        if not queued_missions:
            return None

        return max(
            queued_missions,
            key=lambda mission: mission["priority"],
        )

    def create_pose(
        self,
        station_name: str,
    ) -> PoseStamped:
        if station_name not in STATIONS:
            raise ValueError(
                f"Unknown station: {station_name}"
            )

        x, y, yaw = STATIONS[station_name]

        pose = PoseStamped()

        pose.header.frame_id = "map"
        pose.header.stamp = (
            self.navigator.get_clock()
            .now()
            .to_msg()
        )

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0

        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(
            yaw / 2.0
        )
        pose.pose.orientation.w = math.cos(
            yaw / 2.0
        )

        return pose

    def navigate_to_station(
        self,
        station_name: str,
    ) -> bool:
        goal = self.create_pose(
            station_name
        )

        print(
            f"Sending Nav2 goal: {station_name} "
            f"x={goal.pose.position.x:.2f}, "
            f"y={goal.pose.position.y:.2f}"
        )

        self.navigator.goToPose(
            goal
        )

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()

            if feedback is not None:
                distance_remaining = getattr(
                    feedback,
                    "distance_remaining",
                    None,
                )

                if distance_remaining is not None:
                    print(
                        "Distance remaining: "
                        f"{distance_remaining:.2f} m"
                    )

            time.sleep(0.5)

        result = self.navigator.getResult()

        if result == TaskResult.SUCCEEDED:
            print(
                f"Reached station: {station_name}"
            )
            return True

        if result == TaskResult.CANCELED:
            print(
                f"Navigation canceled: {station_name}"
            )
            return False

        if result == TaskResult.FAILED:
            print(
                f"Navigation failed: {station_name}"
            )
            return False

        print(
            f"Unknown navigation result: {result}"
        )
        return False

    def mark_mission_failed(
        self,
        mission: dict[str, Any],
    ) -> None:
        mission_id = mission["mission_id"]

        self.update_status(
            mission_id,
            "FAILED",
        )

        print("Status -> FAILED")

        self.publish_telemetry(
            mission,
            "FAILED",
        )

    def execute_mission(
        self,
        mission: dict[str, Any],
    ) -> None:
        mission_id = mission["mission_id"]

        print()
        print("=" * 60)
        print(f"Mission:  {mission_id}")
        print(f"Robot:    {mission['robot_id']}")
        print(f"Pickup:   {mission['pickup']}")
        print(f"Dropoff:  {mission['dropoff']}")
        print(f"Priority: {mission['priority']}")
        print("=" * 60)

        try:
            self.create_pose(
                mission["pickup"]
            )

            self.create_pose(
                mission["dropoff"]
            )

            if not self.check_station_available():
                print(
                    "Mission remains QUEUED: "
                    "assembly station is unavailable"
                )
                return

            self.update_status(
                mission_id,
                "ASSIGNED",
            )

            print("Status -> ASSIGNED")

            self.publish_telemetry(
                mission,
                "ASSIGNED",
            )

            self.update_status(
                mission_id,
                "RUNNING",
            )

            print("Status -> RUNNING")

            self.publish_telemetry(
                mission,
                "NAVIGATING_TO_PICKUP",
            )

            print()
            print(
                "Navigating to pickup: "
                f"{mission['pickup']}"
            )

            pickup_success = (
                self.navigate_to_station(
                    mission["pickup"]
                )
            )

            if not pickup_success:
                self.mark_mission_failed(
                    mission
                )
                return

            self.publish_telemetry(
                mission,
                "AT_PICKUP",
            )

            print()
            print(
                "Pickup reached. "
                "Simulating material loading..."
            )

            time.sleep(2.0)

            self.publish_telemetry(
                mission,
                "NAVIGATING_TO_DROPOFF",
            )

            print()
            print(
                "Navigating to dropoff: "
                f"{mission['dropoff']}"
            )

            dropoff_success = (
                self.navigate_to_station(
                    mission["dropoff"]
                )
            )

            if not dropoff_success:
                self.mark_mission_failed(
                    mission
                )
                return

            self.publish_telemetry(
                mission,
                "AT_DROPOFF",
            )

            print()
            print(
                "Dropoff reached."
            )

            self.occupy_station(
                mission["robot_id"]
            )

            print(
                "Simulating material unloading..."
            )

            time.sleep(2.0)

            self.release_station()

            self.update_status(
                mission_id,
                "COMPLETED",
            )

            print("Status -> COMPLETED")

            self.publish_telemetry(
                mission,
                "COMPLETED",
            )

        except ValueError as error:
            print(
                "Mission configuration error: "
                f"{error}"
            )

            self.mark_mission_failed(
                mission
            )

        except httpx.HTTPError as error:
            print(
                "WMS communication error during mission: "
                f"{error}"
            )

        except Exception as error:
            print(
                "Unexpected mission execution error: "
                f"{error}"
            )

            try:
                self.mark_mission_failed(
                    mission
                )

            except httpx.HTTPError as status_error:
                print(
                    "Could not report FAILED status "
                    f"to WMS: {status_error}"
                )

    def run(self) -> None:
        print(
            "MiniFactory Fleet Manager started"
        )

        print(
            f"WMS: {self.wms_url}"
        )

        print(
            "Waiting for Nav2..."
        )

        self.navigator.waitUntilNav2Active()

        print(
            "Nav2 is active"
        )

        print(
            f"Polling every "
            f"{POLL_INTERVAL_SECONDS:.1f} s"
        )

        try:
            while True:
                try:
                    missions = (
                        self.get_missions()
                    )

                    mission = (
                        self.find_next_mission(
                            missions
                        )
                    )

                    if mission is not None:
                        self.execute_mission(
                            mission
                        )

                except httpx.HTTPError as error:
                    print(
                        "WMS communication error: "
                        f"{error}"
                    )

                time.sleep(
                    POLL_INTERVAL_SECONDS
                )

        except KeyboardInterrupt:
            print()
            print(
                "Fleet Manager stopped"
            )

        finally:
            self.client.close()


def main() -> None:
    rclpy.init()

    navigator = BasicNavigator(
        node_name="mini_factory_fleet_manager"
    )

    telemetry = TelemetryPublisher(
        host="localhost",
        port=1883,
    )

    station = OpcUaStationClient()

    try:
        telemetry.connect()

        print(
            "MQTT connected: localhost:1883"
        )

        fleet_manager = FleetManager(
            WMS_URL,
            navigator,
            telemetry,
            station,
        )

        fleet_manager.run()

    except KeyboardInterrupt:
        print()
        print(
            "Fleet Manager interrupted"
        )

    finally:
        telemetry.close()

        navigator.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
