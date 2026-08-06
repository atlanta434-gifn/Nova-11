from typing import Dict, Any, List


class CostEngine:
    """محرك تقدير التكاليف وحساب الكميات (BOQ)"""

    UNIT_COSTS = {
        "concrete_c30": 120.0,
        "steel_rebar": 800.0,
        "blockwork": 25.0,
        "plastering": 8.0,
        "painting": 5.0,
        "flooring_ceramic": 20.0,
        "windows_alum": 150.0,
        "doors_wood": 200.0,
        "electrical_pt": 35.0,
        "plumbing_pt": 45.0,
        "hvac_ton": 800.0,
    }

    def __init__(self):
        self.currency = "USD"
        self.margin = 0.15
        self.contingency = 0.05

    def calculate_cost(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب التكلفة التقديرية بناءً على مساحة المبنى وعدد الغرف"""
        total_area = sum(r.get("area", 0) for r in building_data.get("rooms", []))
        if total_area == 0:
            total_area = building_data.get("total_area", 100)

        floors = building_data.get("total_floors", 1)
        b_type = building_data.get("building_type", "residential")

        concrete_vol = total_area * 0.35 * floors
        steel_ton = concrete_vol * 0.12
        walls_area = total_area * 2.8 * floors
        windows_area = total_area * 0.15 * floors
        doors_count = len(building_data.get("rooms", [])) * floors + 2
        elec_points = int(total_area * 0.8 * floors)
        plumb_points = int((total_area / 50) * 4 * floors)
        hvac_tons = total_area / 15 * floors

        costs = {
            "concrete": concrete_vol * self.UNIT_COSTS["concrete_c30"],
            "steel": steel_ton * self.UNIT_COSTS["steel_rebar"],
            "walls": walls_area * self.UNIT_COSTS["blockwork"],
            "finishes": total_area * floors * (self.UNIT_COSTS["plastering"] + self.UNIT_COSTS["painting"] + self.UNIT_COSTS["flooring_ceramic"]),
            "doors_windows": windows_area * self.UNIT_COSTS["windows_alum"] + doors_count * self.UNIT_COSTS["doors_wood"],
            "electrical": elec_points * self.UNIT_COSTS["electrical_pt"],
            "plumbing": plumb_points * self.UNIT_COSTS["plumbing_pt"],
            "hvac": hvac_tons * self.UNIT_COSTS["hvac_ton"],
        }

        subtotal = sum(costs.values())

        if b_type == "commercial":
            subtotal *= 1.2
        elif b_type == "tower":
            subtotal *= 1.5

        contractor_margin = subtotal * self.margin
        contingency_cost = subtotal * self.contingency
        total = subtotal + contractor_margin + contingency_cost

        return {
            "subtotal": subtotal,
            "margin": contractor_margin,
            "contingency": contingency_cost,
            "total": total,
            "breakdown": costs,
            "metrics": {
                "cost_per_m2": total / (total_area * floors) if total_area > 0 else 0,
                "concrete_vol": concrete_vol,
                "steel_ton": steel_ton,
            }
        }
