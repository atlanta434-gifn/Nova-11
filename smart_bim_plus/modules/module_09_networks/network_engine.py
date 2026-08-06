import numpy as np
from typing import Dict, Any, List, Tuple
import math

class NetworkEngine:
    """محرك حساب وتوزيع شبكات الاتصالات والإنترنت في المبنى"""

    def __init__(self, building_data: Dict[str, Any]):
        """تهيئة المحرك ببيانات المبنى"""
        self.building_data = building_data
        self.grid_resolution = 0.5
        self.wifi_standards = {
            "WiFi 5": {"n": 3.0, "p0": -40.0},
            "WiFi 6": {"n": 2.7, "p0": -35.0},
            "WiFi 6E": {"n": 3.2, "p0": -42.0}
        }
        self.wall_materials = {
            "خرسانة": 12.0,
            "طابوق": 6.0,
            "جدران جافة": 3.0,
            "زجاج": 2.0
        }
        self.plot_width = float(building_data.get("plot_width", 50.0))
        self.plot_length = float(building_data.get("plot_length", 50.0))
        self.rooms = building_data.get("rooms", [])

    def _get_walls(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """استخراج الجدران من بيانات الغرف"""
        walls = []
        for room in self.rooms:
            px = float(room.get("position_x", 0.0))
            py = float(room.get("position_y", 0.0))
            w = float(room.get("width", 5.0))
            l = float(room.get("length", 5.0))
            walls.append(((px, py), (px + w, py)))
            walls.append(((px + w, py), (px + w, py + l)))
            walls.append(((px + w, py + l), (px, py + l)))
            walls.append(((px, py + l), (px, py)))
        return walls

    def _intersect(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """التحقق من تقاطع خطين"""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    def _count_walls(self, p1: Tuple[float, float], p2: Tuple[float, float], walls: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> int:
        """حساب عدد الجدران المتقاطعة"""
        count = 0
        for w1, w2 in walls:
            if self._intersect(p1, p2, w1, w2):
                count += 1
        return count // 2

    def generate_network(self, standard: str, wall_material: str, target_coverage: float, router_power: float) -> Dict[str, Any]:
        """توليد التوزيع الأمثل لنقاط الوصول وحساب الكابلات"""
        width_cells = int(self.plot_width / self.grid_resolution)
        length_cells = int(self.plot_length / self.grid_resolution)
        
        candidates = []
        for room in self.rooms:
            px = float(room.get("position_x", 0.0))
            py = float(room.get("position_y", 0.0))
            w = float(room.get("width", 5.0))
            l = float(room.get("length", 5.0))
            candidates.append((px + w/2, py + l/2))
            
        std_params = self.wifi_standards.get(standard, self.wifi_standards["WiFi 6"])
        n_val = std_params["n"]
        p0 = std_params["p0"] + (router_power - 20.0) 
        attenuation = self.wall_materials.get(wall_material, 6.0)
        walls = self._get_walls()

        coverage_matrix = {}
        for idx, (cx, cy) in enumerate(candidates):
            covered = set()
            for i in range(width_cells):
                for j in range(length_cells):
                    gx = i * self.grid_resolution
                    gy = j * self.grid_resolution
                    dist = math.hypot(gx - cx, gy - cy)
                    if dist < 1.0:
                        dist = 1.0
                    wall_count = self._count_walls((cx, cy), (gx, gy), walls)
                    signal = p0 - 10 * n_val * math.log10(dist) - (wall_count * attenuation)
                    if signal >= target_coverage:
                        covered.add((i, j))
            coverage_matrix[idx] = covered

        uncovered = set((i, j) for i in range(width_cells) for j in range(length_cells))
        selected_aps = []
        
        while uncovered:
            best_ap = None
            best_cover = set()
            for idx, cover in coverage_matrix.items():
                current_cover = cover.intersection(uncovered)
                if len(current_cover) > len(best_cover):
                    best_cover = current_cover
                    best_ap = idx
            
            if not best_ap and best_ap != 0:
                break
                
            selected_aps.append(candidates[best_ap])
            uncovered -= best_cover
            del coverage_matrix[best_ap]

        if not selected_aps:
            selected_aps = [(self.plot_width / 2, self.plot_length / 2)]

        heatmap = np.zeros((length_cells, width_cells))
        for i in range(width_cells):
            for j in range(length_cells):
                gx = i * self.grid_resolution
                gy = j * self.grid_resolution
                max_sig = -100.0
                for cx, cy in selected_aps:
                    dist = math.hypot(gx - cx, gy - cy)
                    if dist < 1.0:
                        dist = 1.0
                    wall_count = self._count_walls((cx, cy), (gx, gy), walls)
                    signal = p0 - 10 * n_val * math.log10(dist) - (wall_count * attenuation)
                    if signal > max_sig:
                        max_sig = signal
                heatmap[j, i] = max_sig

        server_room = (5.0, 5.0)
        if self.rooms:
            r = self.rooms[0]
            server_room = (float(r.get("position_x", 0.0)) + float(r.get("width", 5.0))/2,
                           float(r.get("position_y", 0.0)) + float(r.get("length", 5.0))/2)

        nodes = [server_room] + selected_aps
        edges = []
        visited = set([0])
        unvisited = set(range(1, len(nodes)))
        total_cable = 0.0

        while unvisited:
            min_dist = float('inf')
            best_edge = None
            for u in visited:
                for v in unvisited:
                    d = math.hypot(nodes[u][0] - nodes[v][0], nodes[u][1] - nodes[v][1])
                    if d < min_dist:
                        min_dist = d
                        best_edge = (u, v)
            if best_edge:
                edges.append((nodes[best_edge[0]], nodes[best_edge[1]]))
                visited.add(best_edge[1])
                unvisited.remove(best_edge[1])
                total_cable += min_dist

        switches_needed = max(1, math.ceil(len(selected_aps) / 8))

        return {
            "access_points": selected_aps,
            "heatmap": heatmap,
            "cables": edges,
            "total_cable_length": total_cable * 1.2,
            "switches": switches_needed,
            "server_room": server_room,
            "grid_res": self.grid_resolution,
            "cost": (len(selected_aps) * 150) + (total_cable * 1.2 * 2) + (switches_needed * 200)
        }
