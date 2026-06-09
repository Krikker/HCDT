from app.models import SensorSnapshot


class SCADAAdapter:
    """
    Demo SCADA/IIoT adapter.
    A production version would aggregate OPC UA and MQTT streams.
    """

    def get_snapshot(self, station_id: str) -> SensorSnapshot:
        if station_id == "st-weld-body":
            return SensorSnapshot(
                station_id=station_id,
                tool_connected="thermal-scanner",
                torque_ok=True,
                lighting_ok=True,
                noise_level=0.84,
                cycle_deviation_sec=38,
                micro_pause_minutes=2,
            )

        if station_id == "st-engine":
            return SensorSnapshot(
                station_id=station_id,
                tool_connected="angle-gauge",
                torque_ok=False,
                lighting_ok=True,
                noise_level=0.57,
                cycle_deviation_sec=29,
                micro_pause_minutes=5,
            )

        if station_id == "st-paint":
            return SensorSnapshot(
                station_id=station_id,
                tool_connected="tablet",
                torque_ok=True,
                lighting_ok=False,
                noise_level=0.41,
                cycle_deviation_sec=19,
                micro_pause_minutes=6,
            )

        if station_id == "st-door":
            return SensorSnapshot(
                station_id=station_id,
                tool_connected="scanner",
                torque_ok=False,
                lighting_ok=True,
                noise_level=0.72,
                cycle_deviation_sec=41,
                micro_pause_minutes=3,
            )

        if station_id == "st-qc":
            return SensorSnapshot(
                station_id=station_id,
                tool_connected="tablet",
                torque_ok=True,
                lighting_ok=True,
                noise_level=0.36,
                cycle_deviation_sec=12,
                micro_pause_minutes=8,
            )

        return SensorSnapshot(
            station_id=station_id,
            tool_connected="scanner",
            torque_ok=True,
            lighting_ok=True,
            noise_level=0.48,
            cycle_deviation_sec=24,
            micro_pause_minutes=4,
        )
