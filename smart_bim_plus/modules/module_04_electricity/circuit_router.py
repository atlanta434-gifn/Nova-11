import networkx as nx
import numpy as np
from typing import List, Dict, Any, Tuple


class CircuitRouter:
    """خوارزمية توجيه الدوائر الكهربائية"""

    def __init__(self):
        self.graph = nx.Graph()
        self.voltage = 230.0
        self.max_voltage_drop = 0.03
        self.copper_resistivity = 0.01724

    def route_circuits(self, room_loads: List[Dict[str, Any]],
                       panel_position: Tuple[float, float]) -> Dict[str, Any]:
        """توزيع الغرف على الدوائر وتوجيه الأسلاك"""
        circuits = []
        current_circuit = []
        current_load = 0.0
        max_circuit_load = 3000.0

        sorted_rooms = sorted(
            room_loads, key=lambda x: x["active_watt"], reverse=True
        )

        for room in sorted_rooms:
            load = room["active_watt"]

            if load > max_circuit_load:
                circuits.append({
                    "id": len(circuits) + 1,
                    "rooms": [room["room_name"]],
                    "load_w": load,
                    "current": load / self.voltage,
                    "breaker": 20 if load / self.voltage > 10 else 16,
                    "wire_mm2": self._select_wire(load / self.voltage),
                    "type": "dedicated",
                })
                continue

            if current_load + load > max_circuit_load:
                if current_circuit:
                    circuits.append({
                        "id": len(circuits) + 1,
                        "rooms": [r["room_name"] for r in current_circuit],
                        "load_w": current_load,
                        "current": current_load / self.voltage,
                        "breaker": 16,
                        "wire_mm2": self._select_wire(current_load / self.voltage),
                        "type": "mixed",
                    })
                current_circuit = [room]
                current_load = load
            else:
                current_circuit.append(room)
                current_load += load

        if current_circuit:
            circuits.append({
                "id": len(circuits) + 1,
                "rooms": [r["room_name"] for r in current_circuit],
                "load_w": current_load,
                "current": current_load / self.voltage,
                "breaker": 16,
                "wire_mm2": self._select_wire(current_load / self.voltage),
                "type": "mixed",
            })

        return {
            "circuits": circuits,
            "panel_position": panel_position,
            "total_circuits": len(circuits),
        }

    def _select_wire(self, current: float) -> float:
        if current <= 10:
            return 1.5
        elif current <= 16:
            return 2.5
        elif current <= 25:
            return 4.0
        elif current <= 32:
            return 6.0
        elif current <= 40:
            return 10.0
        elif current <= 63:
            return 16.0
        return 25.0
