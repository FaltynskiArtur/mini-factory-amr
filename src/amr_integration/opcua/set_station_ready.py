import argparse
import asyncio

from asyncua import Client, ua


OPC_UA_URL = "opc.tcp://localhost:4840/mini-factory/"
NAMESPACE_URI = "urn:mini-factory:station"


async def set_station_ready(value: bool) -> None:
    async with Client(url=OPC_UA_URL) as client:
        namespace_index = await client.get_namespace_index(
            NAMESPACE_URI
        )

        station_ready = client.get_node(
            f"ns={namespace_index};"
            "s=AssemblyStation01.StationReady"
        )

        await station_ready.write_value(
            ua.Variant(
                value,
                ua.VariantType.Boolean,
            )
        )

        print(
            f"StationReady -> {value}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "state",
        choices=("true", "false"),
    )

    args = parser.parse_args()

    value = args.state == "true"

    asyncio.run(
        set_station_ready(value)
    )


if __name__ == "__main__":
    main()
