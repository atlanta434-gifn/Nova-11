from typing import List, Dict, Any
import numpy as np


class LoadCalculator:
    """حاسبة الأحمال الكهربائية"""

    APPLIANCE_LOADS = {
        "lighting": {"load_w": 20, "pf": 0.9, "factor": 0.8},
        "ac_split": {"load_w": 2500, "pf": 0.85, "factor": 0.7},
        "refrigerator": {"load_w": 500, "pf": 0.8, "factor": 0.5},
        "tv": {"load_w": 150, "pf": 0.95, "factor": 0.6},
        "pc": {"load_w": 300, "pf": 0.9, "factor": 0.6},
        "water_heater": {"load_w": 3000, "pf": 1.0, "factor": 0.4},
        "washing_machine": {"load_w": 1500, "pf": 0.8, "factor": 0.3},
        "microwave": {"load_w": 1200, "pf": 0.95, "factor": 0.2},
        "general_socket": {"load_w": 200, "pf": 0.9, "factor": 0.4},
    }

    ROOM_DEFAULTS = {
        "living_room": ["lighting", "ac_split", "tv", "general_socket", "general_socket"],
        "bedroom": ["lighting", "ac_split", "general_socket"],
        "master_bedroom": ["lighting", "ac_split", "tv", "general_socket", "general_socket"],
        "kitchen": ["lighting", "refrigerator", "microwave", "general_socket", "general_socket", "general_socket"],
        "bathroom": ["lighting", "water_heater", "general_socket"],
        "corridor": ["lighting", "general_socket"],
        "office": ["lighting", "ac_split", "pc", "pc", "general_socket", "general_socket"],
    }

    def __init__(self):
        self.voltage = 230.0
        self.solar_panel_w = 400.0

    def calculate_room_load(self, room: Dict[str, Any]) -> Dict[str, Any]:
        """حساب أحمال غرفة مفردة"""
        rt = room.get("room_type", "storage")
        area = room.get("area", 10.0)

        appliances = self.ROOM_DEFAULTS.get(rt, ["lighting", "general_socket"])

        total_w = 0.0
        total_va = 0.0
        active_w = 0.0

        lighting_w = area * self.APPLIANCE_LOADS["lighting"]["load_w"]
        lighting_va = lighting_w / self.APPLIANCE_LOADS["lighting"]["pf"]

        total_w += lighting_w
        total_va += lighting_va
        active_w += lighting_w * self.APPLIANCE_LOADS["lighting"]["factor"]

        app_details = []

        for app in appliances:
            if app == "lighting":
                continue
            data = self.APPLIANCE_LOADS.get(app)
            if data:
                w = data["load_w"]
                va = w / data["pf"]
                total_w += w
                total_va += va
                active_w += w * data["factor"]
                app_details.append({
                    "name": app,
                    "watt": w,
                    "va": va,
                    "current": va / self.voltage
                })

        total_current = total_va / self.voltage
        active_current = active_w / self.voltage

        return {
            "room_name": room.get("name", rt),
            "area": area,
            "appliances": app_details,
            "total_watt": total_w,
            "total_va": total_va,
            "active_watt": active_w,
            "total_current": total_current,
            "active_current": active_current,
        }

    def calculate_building_load(self, rooms: List[Dict[str, Any]],
                                solar_percent: float = 0.0) -> Dict[str, Any]:
        """حساب الأحمال الكلية للمبنى وتوزيع الألواح الشمسية"""
        room_loads = []
        total_w = 0.0
        total_va = 0.0
        active_w = 0.0

        for room in rooms:
            rl = self.calculate_room_load(room)
            room_loads.append(rl)
            total_w += rl["total_watt"]
            total_va += rl["total_va"]
            active_w += rl["active_watt"]

        demand_factor = 0.8
        if total_w > 20000:
            demand_factor = 0.6
        elif total_w > 10000:
            demand_factor = 0.7

        design_w = total_w * demand_factor
        design_va = total_va * demand_factor
        design_current = design_va / self.voltage

        solar_required_w = design_w * (solar_percent / 100.0)
        num_panels = int(np.ceil(solar_required_w / self.solar_panel_w))
        solar_capacity = num_panels * self.solar_panel_w

        main_breaker = self._select_breaker(design_current)

        return {
            "room_loads": room_loads,
            "total_installed_watt": total_w,
            "total_installed_va": total_va,
            "design_watt": design_w,
            "design_va": design_va,
            "design_current": design_current,
            "main_breaker_amp": main_breaker,
            "solar_target_percent": solar_percent,
            "solar_panels_count": num_panels,
            "solar_capacity_watt": solar_capacity,
            "phase_type": "3-Phase" if design_current > 100 else "1-Phase",
        }

    def _select_breaker(self, current: float) -> int:
        standards = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400]
        margin_current = current * 1.25
        for b in standards:
            if b >= margin_current:
                return b
        return standards[-1]
