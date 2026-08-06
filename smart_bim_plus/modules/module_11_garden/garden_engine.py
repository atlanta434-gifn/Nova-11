import math
import numpy as np
from typing import Dict, Any, List, Tuple
from collections import defaultdict

class GardenEngine:
    """محرك الحديقة الذكية لحسابات الري والنباتات"""
    
    def __init__(self, building_data: Dict[str, Any]):
        self.data = building_data
        self.plot_width = float(building_data.get("plot_width", 30.0))
        self.plot_length = float(building_data.get("plot_length", 30.0))
        self.rooms = building_data.get("rooms", [])
        
    def calculate_garden_area(self) -> float:
        """حساب مساحة الحديقة"""
        plot_area = self.plot_width * self.plot_length
        building_area = 0.0
        for r in self.rooms:
            building_area += float(r.get("area", r.get("width", 0) * r.get("length", 0)))
        return max(0.0, plot_area - building_area)
        
    def determine_zones(self) -> List[Dict[str, Any]]:
        """تحديد مناطق الحديقة بناء على الإضاءة"""
        zones = []
        total_area = self.calculate_garden_area()
        zones.append({"name": "منطقة شمس كاملة", "exposure": "full_sun", "area": total_area * 0.5})
        zones.append({"name": "منطقة ظل جزئي", "exposure": "partial_shade", "area": total_area * 0.3})
        zones.append({"name": "منطقة ظل كامل", "exposure": "full_shade", "area": total_area * 0.2})
        return zones
        
    def calculate_water_requirement(self, zones: List[Dict[str, Any]], climate: str) -> float:
        """حساب احتياجات المياه باللتر يوميا"""
        et0_map = {"arid": 7.0, "mediterranean": 5.0, "tropical": 4.0}
        et0 = et0_map.get(climate, 5.0)
        
        kc_map = {"full_sun": 0.8, "partial_shade": 0.6, "full_shade": 0.4}
        
        total_water_liters = 0.0
        for z in zones:
            kc = kc_map.get(z["exposure"], 0.6)
            water = z["area"] * et0 * kc
            z["water_req"] = water
            total_water_liters += water
            
        return total_water_liters
        
    def select_plants(self, climate: str, style: str) -> List[str]:
        """اختيار النباتات بناء على المناخ والنمط"""
        plants = []
        if climate == "arid" or style == "xeriscape":
            plants = ["صبار", "أغاف", "لافندر", "إكليل الجبل"]
        elif climate == "tropical":
            plants = ["موز", "نخيل", "سرخس", "بومباكس"]
        else:
            plants = ["ورد", "ياسمين", "فيكس", "زيتون"]
        return plants
        
    def distribute_sprinklers(self, garden_area: float) -> Tuple[List[Tuple[float, float]], float]:
        """توزيع الرشاشات باستخدام خوارزمية دوائر مبسطة"""
        radius = 3.0
        coverage_area = math.pi * (radius ** 2)
        count = max(1, int(math.ceil((garden_area * 1.2) / coverage_area)))
        
        sprinklers = []
        cols = max(1, int(math.sqrt(count * (self.plot_width / self.plot_length))))
        rows = max(1, int(count / cols))
        
        x_step = self.plot_width / (cols + 1)
        y_step = self.plot_length / (rows + 1)
        
        for r in range(rows):
            for c in range(cols):
                px = (c + 1) * x_step
                py = (r + 1) * y_step
                in_building = False
                for rm in self.rooms:
                    rx = float(rm.get("position_x", 0))
                    ry = float(rm.get("position_y", 0))
                    rw = float(rm.get("width", 0))
                    rl = float(rm.get("length", 0))
                    if rx <= px <= rx + rw and ry <= py <= ry + rl:
                        in_building = True
                        break
                if not in_building:
                    sprinklers.append((px, py))
                    
        return sprinklers, radius

    def design_pipe_network(self, sprinklers: List[Tuple[float, float]]) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """تصميم شبكة الأنابيب باستخدام خوارزمية الشجرة الممتدة الصغرى"""
        if not sprinklers:
            return []
            
        nodes = [(0.0, 0.0)] + sprinklers
        edges = []
        
        visited = set([0])
        unvisited = set(range(1, len(nodes)))
        
        while unvisited:
            min_dist = float('inf')
            best_edge = None
            best_u = -1
            
            for v in visited:
                for u in unvisited:
                    dist = math.hypot(nodes[v][0] - nodes[u][0], nodes[v][1] - nodes[u][1])
                    if dist < min_dist:
                        min_dist = dist
                        best_edge = (nodes[v], nodes[u])
                        best_u = u
                        
            if best_edge:
                edges.append(best_edge)
                visited.add(best_u)
                unvisited.remove(best_u)
                
        return edges

    def generate_system(self, climate: str, style: str) -> Dict[str, Any]:
        """توليد مخرجات النظام بالكامل"""
        area = self.calculate_garden_area()
        zones = self.determine_zones()
        water_req = self.calculate_water_requirement(zones, climate)
        plants = self.select_plants(climate, style)
        sprinklers, radius = self.distribute_sprinklers(area)
        pipes = self.design_pipe_network(sprinklers)
        
        pipe_length = sum(math.hypot(p1[0]-p2[0], p1[1]-p2[1]) for p1, p2 in pipes)
        pump_power = (water_req / 1000) * 0.5
        tank_cap = water_req * 2
        
        return {
            "garden_area": area,
            "zones": zones,
            "total_water_liters": water_req,
            "plants": plants,
            "sprinklers": sprinklers,
            "sprinkler_radius": radius,
            "pipes": pipes,
            "total_pipe_length": pipe_length,
            "pump_power_kw": pump_power,
            "tank_capacity_liters": tank_cap,
            "schedule": "الري مرتين يوميا: 5 صباحا و 7 مساء"
        }
