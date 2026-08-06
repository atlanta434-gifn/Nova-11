import numpy as np
import heapq
from typing import Dict, Any, List, Tuple

class HVACEngine:
    """محرك حسابات التكييف والتهوية بناءً على معايير ASHRAE"""
    
    def __init__(self, building_data: Dict[str, Any], outdoor_temp: float, indoor_temp: float, orientation: float, wall_insulation: str, glass_type: str):
        self.building_data = building_data
        self.outdoor_temp = outdoor_temp
        self.indoor_temp = indoor_temp
        self.orientation = orientation
        self.wall_insulation = wall_insulation
        self.glass_type = glass_type
        
        self.results = {}
        self.ducts = []
        self.grid_size = 0.5 

    def calculate_loads(self) -> Dict[str, Any]:
        """حساب الأحمال الحرارية لكل غرفة"""
        u_wall = self._get_wall_u_value()
        shgc = self._get_glass_shgc()
        delta_t = self.outdoor_temp - self.indoor_temp
        
        rooms = self.building_data.get("rooms", [])
        total_load = 0.0
        ac_units = []
        room_loads = []
        
        for room in rooms:
            area = room.get("area", 0.0)
            has_window = room.get("has_window", False)
            
            conduction = u_wall * area * delta_t * 3.412
            
            solar = 0.0
            if has_window:
                window_area = area * 0.1
                solar = shgc * window_area * 500
                
            internal = area * 50
            infiltration = area * 0.1 * delta_t * 1.08
            
            room_load_btu = max(0, conduction + solar + internal + infiltration)
            room_load_ton = room_load_btu / 12000.0
            
            total_load += room_load_btu
            room_loads.append({
                "name": room.get("name", "Unknown"),
                "load_btu": room_load_btu,
                "load_ton": room_load_ton,
                "x": room.get("position_x", 0.0),
                "y": room.get("position_y", 0.0),
                "w": room.get("width", 0.0),
                "l": room.get("length", 0.0)
            })
            
            if room_load_ton > 0.5:
                ac_units.append({
                    "x": room.get("position_x", 0.0) + room.get("width", 0.0) / 2,
                    "y": room.get("position_y", 0.0) + room.get("length", 0.0) / 2,
                    "capacity_ton": np.ceil(room_load_ton * 2) / 2
                })
                
        self.results["room_loads"] = room_loads
        self.results["ac_units"] = ac_units
        self.results["total_load_btu"] = total_load
        
        return self.results

    def route_ducts(self):
        """توجيه مجاري الهواء باستخدام خوارزمية A*"""
        plot_w = self.building_data.get("plot_width", 20.0)
        plot_l = self.building_data.get("plot_length", 20.0)
        
        cols = int(plot_w / self.grid_size)
        rows = int(plot_l / self.grid_size)
        grid = np.zeros((rows, cols))
        
        start = (int(rows/2), int(cols/2))
        
        for ac in self.results.get("ac_units", []):
            end = (int(ac["y"] / self.grid_size), int(ac["x"] / self.grid_size))
            if end[0] >= rows: end = (rows-1, end[1])
            if end[1] >= cols: end = (end[0], cols-1)
            
            path = self._astar(grid, start, end)
            if path:
                real_path = [(p[1]*self.grid_size, p[0]*self.grid_size) for p in path]
                self.ducts.append({
                    "path": real_path,
                    "flow_rate": ac["capacity_ton"] * 400
                })
                
        self.results["ducts"] = self.ducts

    def calculate_duct_sizes(self):
        """حساب مقاسات مجاري الهواء"""
        for duct in self.results.get("ducts", []):
            flow_cfm = duct["flow_rate"]
            velocity_fpm = 1000
            area_sqft = flow_cfm / velocity_fpm
            area_sqin = area_sqft * 144
            
            width = np.sqrt(area_sqin * 1.5)
            height = width / 1.5
            duct["width_in"] = round(width, 1)
            duct["height_in"] = round(height, 1)

    def calculate_efficiency(self):
        """حساب كفاءة الطاقة"""
        seer = 14.0
        if self.wall_insulation == "ممتاز":
            seer += 4.0
        elif self.wall_insulation == "جيد":
            seer += 2.0
            
        if self.glass_type == "مزدوج":
            seer += 2.0
            
        self.results["seer"] = seer
        
        total_btu = self.results.get("total_load_btu", 0.0)
        power_kw = total_btu / (seer * 1000.0)
        self.results["energy_cost_per_hour"] = power_kw * 0.15

    def _get_wall_u_value(self) -> float:
        """الحصول على معامل انتقال الحرارة للجدار"""
        values = {"ضعيف": 2.0, "متوسط": 1.0, "جيد": 0.5, "ممتاز": 0.3}
        return values.get(self.wall_insulation, 1.0)

    def _get_glass_shgc(self) -> float:
        """الحصول على معامل الاكتساب الحراري الشمسي للزجاج"""
        values = {"عادي": 0.8, "مزدوج": 0.5, "عاكس": 0.3}
        return values.get(self.glass_type, 0.8)

    def _astar(self, grid: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """خوارزمية البحث A* للمسارات"""
        rows, cols = grid.shape
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
                
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dr, current[1] + dc)
                
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and grid[neighbor[0], neighbor[1]] == 0:
                    tentative_g_score = g_score[current] + 1
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, end)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        
        return []

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """دالة التقدير التقريبي للخوارزمية"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
