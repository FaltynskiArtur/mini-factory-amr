import asyncio
import logging

from asyncua import Server, ua


OPC_UA_ENDPOINT = "opc.tcp://0.0.0.0:4840/mini-factory/"
NAMESPACE_URI = "urn:mini-factory:station"


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    server = Server()

    await server.init()

    server.set_endpoint(
        OPC_UA_ENDPOINT
    )

    server.set_server_name(
        "MiniFactory Station PLC"
    )

    namespace_index = await server.register_namespace(
        NAMESPACE_URI
    )

    station = await server.nodes.objects.add_object(
        namespace_index,
        "AssemblyStation01",
    )

    station_ready = await station.add_variable(
        ua.NodeId(
            "AssemblyStation01.StationReady",
            namespace_index,
        ),
        "StationReady",
        True,
    )

    robot_present = await station.add_variable(
        ua.NodeId(
            "AssemblyStation01.RobotPresent",
            namespace_index,
        ),
        "RobotPresent",
        False,
    )

    mission_active = await station.add_variable(
        ua.NodeId(
            "AssemblyStation01.MissionActive",
            namespace_index,
        ),
        "MissionActive",
        False,
    )

    emergency_stop = await station.add_variable(
        ua.NodeId(
            "AssemblyStation01.EmergencyStop",
            namespace_index,
        ),
        "EmergencyStop",
        False,
    )

    robot_id = await station.add_variable(
        ua.NodeId(
            "AssemblyStation01.RobotId",
            namespace_index,
        ),
        "RobotId",
        "",
    )

    await station_ready.set_writable()
    await robot_present.set_writable()
    await mission_active.set_writable()
    await emergency_stop.set_writable()
    await robot_id.set_writable()

    print()
    print("=" * 60)
    print("MiniFactory OPC UA Station PLC")
    print("=" * 60)
    print(
        "Endpoint: "
        "opc.tcp://localhost:4840/mini-factory/"
    )
    print("Object: AssemblyStation01")
    print()
    print("Variables:")
    print("  StationReady  = True")
    print("  RobotPresent  = False")
    print("  MissionActive = False")
    print("  EmergencyStop = False")
    print("  RobotId       = ''")
    print("=" * 60)
    print()

    async with server:
        while True:
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("OPC UA Station PLC stopped")