import numpy as np
import math
from typing import Dict, Any, Tuple

class LightingEngine:
    """محرك حسابات الإضاءة الطبيعية والصناعية"""
    
    def __init__(self, latitude: float, longitude: float):
        """تهيئة المحرك مع الإحداثيات الجغرافية"""
        self.latitude = latitude
        self.longitude = longitude
        
    def calculate_sun_position(self, month: int, day: int, hour: float) -> Tuple[float, float]:
        """حساب موقع الشمس (السمت والارتفاع)"""
        day_of_year = int(30.4 * (month - 1) + day)
        declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))
        
        lstm = 15 * round(self.longitude / 15)
        b = math.radians(360 / 364 * (day_of_year - 81))
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        tc = 4 * (self.longitude - lstm) + eot
        lst = hour + tc / 60
        hour_angle = 15 * (lst - 12)
        
        lat_rad = math.radians(self.latitude)
        dec_rad = math.radians(declination)
        ha_rad = math.radians(hour_angle)
        
        alt_rad = math.asin(max(-1.0, min(1.0, math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad))))
        
        cos_az = (math.sin(dec_rad) - math.sin(alt_rad) * math.sin(lat_rad)) / (math.cos(alt_rad) * math.cos(lat_rad) + 0.0001)
        az_rad = math.acos(max(-1.0, min(1.0, cos_az)))
        
        if hour_angle > 0:
            az_rad = 2 * math.pi - az_rad
            
        return math.degrees(az_rad), math.degrees(alt_rad)
        
    def calculate_daylight_factor(self, room: Dict[str, Any], sky_condition: str) -> float:
        """حساب عامل ضوء النهار للغرفة"""
        has_window = room.get("has_window", False)
        if not has_window:
            return 0.5
            
        area = room.get("area", 10.0)
        window_area = area * 0.15
        
        t = 0.7
        aw = window_area
        a = area * 3.0
        r = 0.5
        
        df = (t * aw * 100) / (a * (1 - r**2))
        
        if sky_condition == "clear":
            df *= 1.2
        elif sky_condition == "overcast":
            df *= 0.8
            
        return df
        
    def calculate_room_illuminance(self, room: Dict[str, Any], df: float, sun_alt: float) -> Tuple[np.ndarray, Dict[str, Any]]:
        """حساب توزيع الإضاءة والاحتياجات الصناعية"""
        width = room.get("width", 5.0)
        length = room.get("length", 5.0)
        
        external_illuminance = max(1000, 10000 * math.sin(math.radians(max(0, sun_alt))))
        base_lux = external_illuminance * (df / 100)
        
        grid_x = int(math.ceil(width / 0.5))
        grid_y = int(math.ceil(length / 0.5))
        grid_x = max(1, grid_x)
        grid_y = max(1, grid_y)
        
        illuminance_grid = np.zeros((grid_y, grid_x))
        
        for i in range(grid_y):
            for j in range(grid_x):
                dist = (i + 0.5) * 0.5
                factor = math.exp(-0.3 * dist)
                illuminance_grid[i, j] = base_lux * factor + 50
                
        avg_lux = float(np.mean(illuminance_grid))
        
        artificial_needs = {}
        if avg_lux < 300:
            deficit = 300 - avg_lux
            total_lumens_needed = deficit * room.get("area", width * length) / 0.8 / 0.6
            fixtures = math.ceil(total_lumens_needed / 3000)
            artificial_needs = {
                "fixtures": fixtures,
                "wattage": fixtures * 30
            }
        else:
            artificial_needs = {
                "fixtures": 0,
                "wattage": 0
            }
            
        return illuminance_grid, artificial_needs
        
    def run_analysis(self, building_data: Dict[str, Any], month: int, day: int, hour: float, sky_condition: str) -> Dict[str, Any]:
        """تنفيذ التحليل الشامل للمبنى"""
        sun_az, sun_alt = self.calculate_sun_position(month, day, hour)
        
        results = {
            "sun_position": {"azimuth": sun_az, "altitude": sun_alt},
            "rooms": []
        }
        
        rooms = building_data.get("rooms", [])
        for room in rooms:
            df = self.calculate_daylight_factor(room, sky_condition)
            grid, artificial = self.calculate_room_illuminance(room, df, sun_alt)
            results["rooms"].append({
                "room_data": room,
                "daylight_factor": df,
                "illuminance_grid": grid,
                "artificial_lighting": artificial
            })
            
        return results
