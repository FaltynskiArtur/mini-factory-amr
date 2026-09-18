import asyncio
from dataclasses import dataclass

from asyncua import Client, ua


OPC_UA_URL = "opc.tcp://localhost:4840/mini-factory/"
NAMESPACE_URI = "urn:mini-factory:station"


@dataclass(frozen=True)
class StationState:
    station_ready: bool
    robot_present: bool
    mission_active: bool
    emergency_stop: bool
    robot_id: str


class OpcUaStationClient:
    def __init__(
        self,
        url: str = OPC_UA_URL,
        namespace_uri: str = NAMESPACE_URI,
    ) -> None:
        self.url = url
        self.namespace_uri = namespace_uri

    async def _get_nodes(
        self,
        client: Client,
    ) -> dict[str, object]:
        namespace_index = (
            await client.get_namespace_index(
                self.namespace_uri
            )
        )

        def get_node(name: str):
            return client.get_node(
                f"ns={namespace_index};"
                f"s=AssemblyStation01.{name}"
            )

        return {
            "station_ready": get_node(
                "StationReady"
            ),
            "robot_present": get_node(
                "RobotPresent"
            ),
            "mission_active": get_node(
                "MissionActive"
            ),
            "emergency_stop": get_node(
                "EmergencyStop"
            ),
            "robot_id": get_node(
                "RobotId"
            ),
        }

    async def _read_state(
        self,
    ) -> StationState:
        async with Client(
            url=self.url
        ) as client:
            nodes = await self._get_nodes(
                client
            )

            return StationState(
                station_ready=await nodes[
                    "station_ready"
                ].read_value(),
                robot_present=await nodes[
                    "robot_present"
                ].read_value(),
                mission_active=await nodes[
                    "mission_active"
                ].read_value(),
                emergency_stop=await nodes[
                    "emergency_stop"
                ].read_value(),
                robot_id=await nodes[
                    "robot_id"
                ].read_value(),
            )

    async def _set_robot_state(
        self,
        robot_id: str,
        robot_present: bool,
        mission_active: bool,
    ) -> None:
        async with Client(
            url=self.url
        ) as client:
            nodes = await self._get_nodes(
                client
            )

            await nodes[
                "robot_present"
            ].write_value(
                ua.Variant(
                    robot_present,
                    ua.VariantType.Boolean,
                )
            )

            await nodes[
                "mission_active"
            ].write_value(
                ua.Variant(
                    mission_active,
                    ua.VariantType.Boolean,
                )
            )

            await nodes[
                "robot_id"
            ].write_value(
                ua.Variant(
                    robot_id,
                    ua.VariantType.String,
                )
            )

    def read_state(
        self,
    ) -> StationState:
        return asyncio.run(
            self._read_state()
        )

    def set_robot_state(
        self,
        robot_id: str,
        robot_present: bool,
        mission_active: bool,
    ) -> None:
        asyncio.run(
            self._set_robot_state(
                robot_id=robot_id,
                robot_present=robot_present,
                mission_active=mission_active,
            )
        )