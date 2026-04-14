from __future__ import annotations

import sys
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.plant import TankPlant
from sim.tasks.filter_tank_sequence.runtime import FilterTankPlant
from sim.tasks.mixing_tank_fill_heat.runtime import MixingTankPlant
from sim.tasks.pressure_vessel_interlock.runtime import PressureVesselPlant
from sim.tasks.thermal_chamber_hysteresis.runtime import ThermalChamberPlant


class TankPlantTests(unittest.TestCase):
    def test_pump_off_monotonically_decreases(self) -> None:
        plant = TankPlant(level=10, pump_on=False)
        observed = [plant.level]

        for _ in range(12):
            observed.append(plant.step())

        self.assertEqual(observed, sorted(observed, reverse=True))
        self.assertEqual(observed[-1], 0)

    def test_pump_on_monotonically_increases(self) -> None:
        plant = TankPlant(level=90, pump_on=True)
        observed = [plant.level]

        for _ in range(5):
            observed.append(plant.step())

        self.assertEqual(observed, sorted(observed))
        self.assertEqual(observed[-1], 100)

    def test_repeated_runs_are_deterministic(self) -> None:
        def simulate() -> list[int]:
            plant = TankPlant(level=20, pump_on=True)
            values = [plant.level]
            for _ in range(10):
                values.append(plant.step())
            return values

        self.assertEqual(simulate(), simulate())


class ThermalChamberPlantTests(unittest.TestCase):
    def test_retained_heat_can_keep_temperature_rising_after_heater_off(self) -> None:
        plant = ThermalChamberPlant(temperature_c=50, heater_on=False, retained_heat_c=6)

        observed = [plant.temperature_c]
        for _ in range(3):
            observed.append(plant.step())

        self.assertGreaterEqual(observed[1], observed[0])
        self.assertGreaterEqual(max(observed), 52)

    def test_repeated_runs_are_deterministic(self) -> None:
        def simulate() -> list[int]:
            plant = ThermalChamberPlant(temperature_c=38, heater_on=True, retained_heat_c=0)
            values = [plant.temperature_c]
            for _ in range(6):
                values.append(plant.step())
            return values

        self.assertEqual(simulate(), simulate())


class PressureVesselPlantTests(unittest.TestCase):
    def test_open_door_relieves_pressure(self) -> None:
        plant = PressureVesselPlant(pressure_kpa=60, door_closed=False, compressor_on=False, vent_open=True)

        observed = [plant.pressure_kpa]
        for _ in range(3):
            observed.append(plant.step())

        self.assertEqual(observed, sorted(observed, reverse=True))
        self.assertLess(observed[-1], observed[0])


class MixingTankPlantTests(unittest.TestCase):
    def test_heater_does_not_raise_temperature_below_min_heating_level(self) -> None:
        plant = MixingTankPlant(temp_c=30, level=40, heater_on=True, inlet_open=False)

        observed = [plant.step()[0] for _ in range(3)]

        self.assertLessEqual(max(observed), 30)


class FilterTankPlantTests(unittest.TestCase):
    def test_filter_reduces_turbidity_and_drain_reduces_level(self) -> None:
        plant = FilterTankPlant(turbidity_ntu=80, level=72, filter_on=True, drain_open=True)

        observed_turbidity = [plant.turbidity_ntu]
        observed_level = [plant.level]
        for _ in range(3):
            turbidity, level = plant.step()
            observed_turbidity.append(turbidity)
            observed_level.append(level)

        self.assertEqual(observed_turbidity, sorted(observed_turbidity, reverse=True))
        self.assertEqual(observed_level, sorted(observed_level, reverse=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
