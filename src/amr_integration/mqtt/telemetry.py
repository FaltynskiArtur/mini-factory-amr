import json
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


class TelemetryPublisher:

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
    ) -> None:
        self.host = host
        self.port = port

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2
        )

        self.connected = False

    def connect(self) -> None:
        self.client.connect(
            self.host,
            self.port,
            keepalive=60,
        )

        self.client.loop_start()

        self.connected = True

    def publish_robot_status(
        self,
        robot_id: str,
        status: str,
        mission_id: str | None = None,
    ) -> None:
        if not self.connected:
            raise RuntimeError(
                "MQTT client is not connected"
            )

        topic = f"amr/{robot_id}/telemetry"

        payload = {
            "robot_id": robot_id,
            "status": status,
            "mission_id": mission_id,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        result = self.client.publish(
            topic,
            json.dumps(payload),
            qos=1,
            retain=False,
        )

        result.wait_for_publish()

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(
                f"MQTT publish failed: {result.rc}"
            )

    def close(self) -> None:
        if not self.connected:
            return

        self.client.loop_stop()
        self.client.disconnect()

        self.connected = False
