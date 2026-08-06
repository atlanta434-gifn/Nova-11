import math
import heapq
from typing import List, Dict, Tuple, Any

class GasEngine:
    """محرك حسابات وتوجيه شبكة الغاز مع خوارزميات السلامة"""

    def __init__(self, building_data: Dict[str, Any], gas_type: str, meter_pos: Tuple[float, float], burners: int, heater_type: str):
        self.building_data = building_data
        self.gas_type = gas_type
        self.meter_pos = meter_pos
        self.burners = burners
        self.heater_type = heater_type
        self.grid_size = 0.5
        self.nodes = {}
        self.edges = []
        self.detectors = []
        self.valves = []
        self.ventilations = []
        self.pipes = []
        self.analysis_results = {}

    def run(self) -> Dict[str, Any]:
        """تنفيذ حسابات وتوجيه النظام"""
        consumers = self._identify_consumers()
        if not consumers:
            return self._empty_result()

        grid, max_x, max_y = self._build_grid()
        
        total_load = self._calculate_total_load(len(consumers))
        pipe_diameter = self._calculate_pipe_diameter(total_load)
        
        self.valves.append(self.meter_pos)
        
        for consumer in consumers:
            target = (consumer['center_x'], consumer['center_y'])
            path = self._route_pipe(self.meter_pos, target, grid, max_x, max_y)
            if path:
                self.pipes.append({
                    "path": path,
                    "diameter": pipe_diameter
                })
                self.detectors.append(target)
                
                if len(path) > 10:
                    mid_idx = len(path) // 2
                    self.valves.append(path[mid_idx])

            self._calculate_ventilation(consumer)

        pressure_drop = self._calculate_pressure_drop(total_load, len(self.pipes))
        
        self.analysis_results = {
            "Total Load (BTU/hr)": f"{total_load:.2f}",
            "Main Pipe Diameter (inch)": f"{pipe_diameter:.2f}",
            "Pressure Drop (psi)": f"{pressure_drop:.4f}",
            "System Type": self.gas_type
        }

        return {
            "pipes": self.pipes,
            "detectors": self.detectors,
            "valves": self.valves,
            "ventilations": self.ventilations,
            "analysis": self.analysis_results
        }

    def _empty_result(self) -> Dict[str, Any]:
        """إرجاع نتيجة فارغة في حال عدم وجود غرف مستهلكة"""
        return {
            "pipes": [], "detectors": [], "valves": [], "ventilations": [], "analysis": {}
        }

    def _identify_consumers(self) -> List[Dict[str, Any]]:
        """تحديد الغرف المستهلكة للغاز"""
        consumers = []
        for room in self.building_data.get("rooms", []):
            rtype = room.get("room_type", "").lower()
            if rtype in ["kitchen", "mechanical_room", "مطبخ", "غرفة ميكانيكا"]:
                center_x = room.get("position_x", 0) + room.get("width", 0) / 2.0
                center_y = room.get("position_y", 0) + room.get("length", 0) / 2.0
                consumers.append({
                    "room": room,
                    "center_x": center_x,
                    "center_y": center_y
                })
        return consumers

    def _build_grid(self) -> Tuple[Dict[Tuple[int, int], float], int, int]:
        """بناء شبكة المسارات مع أوزان السلامة"""
        width = self.building_data.get("plot_width", 20.0)
        length = self.building_data.get("plot_length", 20.0)
        max_x = int(width / self.grid_size)
        max_y = int(length / self.grid_size)
        
        grid = {}
        for ix in range(max_x + 1):
            for iy in range(max_y + 1):
                grid[(ix, iy)] = 1.0

        for room in self.building_data.get("rooms", []):
            rtype = room.get("room_type", "").lower()
            rx = room.get("position_x", 0)
            ry = room.get("position_y", 0)
            rw = room.get("width", 0)
            rl = room.get("length", 0)
            
            ix_start = int(rx / self.grid_size)
            iy_start = int(ry / self.grid_size)
            ix_end = int((rx + rw) / self.grid_size)
            iy_end = int((ry + rl) / self.grid_size)
            
            for ix in range(max(0, ix_start), min(max_x + 1, ix_end + 1)):
                for iy in range(max(0, iy_start), min(max_y + 1, iy_end + 1)):
                    if rtype in ["bedroom", "living_room", "غرفة نوم", "صالة", "معيشة"]:
                        grid[(ix, iy)] = float('inf')
                    elif rtype in ["kitchen", "mechanical_room", "مطبخ", "غرفة ميكانيكا"]:
                        grid[(ix, iy)] = 0.5
                    else:
                        grid[(ix, iy)] = 2.0
                        
        return grid, max_x, max_y

    def _route_pipe(self, start: Tuple[float, float], end: Tuple[float, float], grid: Dict[Tuple[int, int], float], max_x: int, max_y: int) -> List[Tuple[float, float]]:
        """توجيه الأنابيب باستخدام خوارزمية A*"""
        start_grid = (int(start[0] / self.grid_size), int(start[1] / self.grid_size))
        end_grid = (int(end[0] / self.grid_size), int(end[1] / self.grid_size))
        
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
            
        open_set = []
        heapq.heappush(open_set, (0, start_grid))
        came_from = {}
        g_score = {start_grid: 0}
        
        while open_set:
            current_cost, current = heapq.heappop(open_set)
            
            if current == end_grid:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_grid)
                path.reverse()
                return [(p[0] * self.grid_size, p[1] * self.grid_size) for p in path]
                
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] <= max_x and 0 <= neighbor[1] <= max_y:
                    weight = grid.get(neighbor, 1.0)
                    if weight == float('inf'):
                        continue
                    tentative_g_score = g_score[current] + weight
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score = tentative_g_score + heuristic(neighbor, end_grid)
                        heapq.heappush(open_set, (f_score, neighbor))
                        
        return []

    def _calculate_total_load(self, consumers_count: int) -> float:
        """حساب إجمالي الحمل بناء على عدد المستهلكين"""
        burner_load = 10000 * self.burners
        heater_load = 40000 if self.heater_type == "Gas" else 0
        return (burner_load + heater_load) * consumers_count

    def _calculate_pipe_diameter(self, load: float) -> float:
        """حساب قطر الأنبوب باستخدام معادلة ويموث المبسطة"""
        if load <= 0:
            return 0.5
        diameter = math.pow((load / 100000.0), 0.381)
        diameters = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        for d in diameters:
            if d >= diameter:
                return d
        return 2.0

    def _calculate_pressure_drop(self, load: float, pipes_count: int) -> float:
        """حساب هبوط الضغط عبر الشبكة"""
        return (load / 100000.0) * 0.05 * max(1, pipes_count)

    def _calculate_ventilation(self, consumer: Dict[str, Any]):
        """حساب فتحات التهوية المطلوبة"""
        room = consumer["room"]
        area = room.get("area", room.get("width", 0) * room.get("length", 0))
        vent_area = area * 0.01
        self.ventilations.append({
            "x": consumer["center_x"],
            "y": consumer["center_y"] + room.get("length", 2) / 2.0,
            "area": vent_area
        })
