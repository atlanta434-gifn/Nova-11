import numpy as np
from typing import Dict, Any, List

class WasteEngine:
    """محرك حسابات نظام إدارة النفايات"""

    def __init__(self, building_data: Dict[str, Any], occupants: int, building_type: str, recycling_policy: str, floors: int):
        self.building_data = building_data
        self.occupants = occupants
        self.building_type = building_type
        self.recycling_policy = recycling_policy
        self.floors = floors
        self.results: Dict[str, Any] = {}

    def calculate(self) -> Dict[str, Any]:
        """إجراء جميع حسابات النفايات"""
        rooms = self.building_data.get("rooms", [])
        total_waste = 0.0
        
        for room in rooms:
            rt = room.get("room_type", "").lower()
            if "kitchen" in rt or "مطبخ" in rt:
                total_waste += 2.5
            elif "bathroom" in rt or "حمام" in rt or "toilet" in rt:
                total_waste += 0.5
            elif "office" in rt or "مكتب" in rt:
                total_waste += 1.0
            else:
                total_waste += 0.5

        if self.occupants > 0:
            occupant_factor = 1.2 if self.building_type == "commercial" else 1.5
            total_waste = max(total_waste, self.occupants * occupant_factor)
            
        daily_total_kg = total_waste * self.floors
        chute_peak_volume = daily_total_kg * 0.15 
        chute_diameter = max(400.0, np.sqrt(chute_peak_volume) * 50.0) 
        
        room_coords = []
        for r in rooms:
            px = float(r.get("position_x", 0.0))
            py = float(r.get("position_y", 0.0))
            w = float(r.get("width", 0.0))
            l = float(r.get("length", 0.0))
            room_coords.append([px + w / 2, py + l / 2])
        
        if room_coords:
            coords_array = np.array(room_coords)
            chute_pos = np.mean(coords_array, axis=0)
        else:
            chute_pos = np.array([5.0, 5.0])
            
        collection_room_area = (daily_total_kg / 100.0) * 2.0 
        collection_room_area = max(10.0, collection_room_area)
        
        ventilation_ach = 10
        room_height = 3.0
        ventilation_flow_rate = collection_room_area * room_height * ventilation_ach
        
        if self.recycling_policy == "advanced":
            paper_bin = daily_total_kg * 0.3
            plastic_bin = daily_total_kg * 0.2
            glass_bin = daily_total_kg * 0.1
            organic_bin = daily_total_kg * 0.25
            general_bin = daily_total_kg * 0.15
            recycling_rate = 85.0
        else:
            paper_bin = daily_total_kg * 0.1
            plastic_bin = daily_total_kg * 0.1
            glass_bin = 0.0
            organic_bin = 0.0
            general_bin = daily_total_kg * 0.8
            recycling_rate = 20.0
            
        compost_size = organic_bin * 0.5 
        
        self.results = {
            "daily_total_kg": daily_total_kg,
            "chute_diameter_mm": chute_diameter,
            "chute_position": (float(chute_pos[0]), float(chute_pos[1])),
            "collection_room_area_m2": collection_room_area,
            "ventilation_flow_m3_h": ventilation_flow_rate,
            "bins": {
                "paper": paper_bin,
                "plastic": plastic_bin,
                "glass": glass_bin,
                "organic": organic_bin,
                "general": general_bin
            },
            "recycling_rate": recycling_rate,
            "compost_size_kg": compost_size,
            "pneumatic_feasible": daily_total_kg > 2000,
            "collection_frequency": "يوميا" if daily_total_kg > 500 else "يوم بعد يوم"
        }
        
        return self.results
