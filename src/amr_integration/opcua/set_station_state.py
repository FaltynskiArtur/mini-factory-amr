import asyncio

from asyncua import Client, ua


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

        robot_present = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.RobotPresent"
        )

        mission_active = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.MissionActive"
        )

        robot_id = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.RobotId"
        )

        await robot_present.write_value(
            ua.Variant(
                True,
                ua.VariantType.Boolean,
            )
        )

        await mission_active.write_value(
            ua.Variant(
                True,
                ua.VariantType.Boolean,
            )
        )

        await robot_id.write_value(
            ua.Variant(
                "AMR_01",
                ua.VariantType.String,
            )
        )

        print("Station state updated")


if __name__ == "__main__":
    asyncio.run(main())