import asyncio

from asyncua import Client


OPC_UA_URL = (
    "opc.tcp://localhost:4840/mini-factory/"
)

NAMESPACE_URI = "urn:mini-factory:station"


async def main() -> None:
    async with Client(
        url=OPC_UA_URL
    ) as client:
        namespace_index = (
            await client.get_namespace_index(
                NAMESPACE_URI
            )
        )

        station_ready = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.StationReady"
        )

        robot_present = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.RobotPresent"
        )

        mission_active = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.MissionActive"
        )

        emergency_stop = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.EmergencyStop"
        )

        robot_id = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.RobotId"
        )

        print(
            "StationReady:",
            await station_ready.read_value(),
        )

        print(
            "RobotPresent:",
            await robot_present.read_value(),
        )

        print(
            "MissionActive:",
            await mission_active.read_value(),
        )

        print(
            "EmergencyStop:",
            await emergency_stop.read_value(),
        )

        print(
            "RobotId:",
            await robot_id.read_value(),
        )


if __name__ == "__main__":
    asyncio.run(main())