from diagnosis.lhs_client import LHSClient


def main():
    print("LibreHardwareService client test starting...")
    print()

    with LHSClient() as client:

        print("[1] LHSClient opening...")
        print("    Open: OK")
        print()
        
        sensors = client.get_sensors()

        print("[2] LHS metadata")
        print(
            f"    Update interval : "
            f"{client.update_interval_ms} ms"
        )
        print(
            f"    Index format    : "
            f"{client.index_format}"
        )
        print()

        print(
            f"[3] Sensors: {len(sensors)}"
        )
        print()

        targets = {
            "cpu_usage": "/intelcpu/0/load/0",
            "cpu_temperature": "/intelcpu/0/temperature/0",
            "gpu_usage": "/gpu-nvidia/0/load/0",
            "gpu_temperature": "/gpu-nvidia/0/temperature/0",
            "memory_usage": "/ram/load/0",
        }

        sensor_map = {
            sensor.get("identifier"): sensor
            for sensor in sensors
        }

        print("[Target Sensors]")

        for name, identifier in targets.items():

            sensor = sensor_map.get(identifier)

            print(name)

            if sensor is None:
                print("  NOT FOUND")
                continue

            print(
                f"  Identifier : "
                f"{sensor.get('identifier')}"
            )
            print(
                f"  Name       : "
                f"{sensor.get('name')}"
            )
            print(
                f"  Type       : "
                f"{sensor.get('sensorType')}"
            )
            print(
                f"  Hardware   : "
                f"{sensor.get('hardwareName')}"
            )
            print(
                f"  Value      : "
                f"{sensor.get('value')}"
            )

        print()
        print("=" * 60)
        print("Test completed successfully.")
        print("=" * 60)


if __name__ == "__main__":
    main()