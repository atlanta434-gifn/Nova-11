"""محرك نظام الأمان والمراقبة"""
import numpy as np
import heapq
import math
from typing import Dict, List, Tuple, Any

class SecurityEngine:
    """فئة تحوي الخوارزميات اللازمة لتوزيع كاميرات المراقبة وحساب التغطية"""

    def __init__(self, building_data: Dict[str, Any]):
        """تهيئة محرك الأمان باستخدام بيانات المبنى"""
        self.building_data = building_data
        self.grid_size = 0.5
        self.width = int(math.ceil(building_data.get('plot_width', 50) / self.grid_size))
        self.length = int(math.ceil(building_data.get('plot_length', 50) / self.grid_size))
        self.grid = np.zeros((self.width, self.length), dtype=int)
        self.coverage_grid = np.zeros((self.width, self.length), dtype=int)
        self.cameras: List[Dict[str, Any]] = []
        self.sensors: List[Dict[str, Any]] = []
        self.cables: List[List[Tuple[float, float]]] = []
        self._build_environment()

    def _build_environment(self) -> None:
        """بناء بيئة ثنائية الأبعاد تعبر عن الجدران والعوائق"""
        for room in self.building_data.get('rooms', []):
            rx = room.get('position_x', 0)
            ry = room.get('position_y', 0)
            rw = room.get('width', 0)
            rl = room.get('length', 0)
            
            sx = max(0, int(rx / self.grid_size))
            sy = max(0, int(ry / self.grid_size))
            ex = min(self.width - 1, int((rx + rw) / self.grid_size))
            ey = min(self.length - 1, int((ry + rl) / self.grid_size))
            
            for i in range(sx, ex + 1):
                self.grid[i, sy] = 1
                self.grid[i, ey] = 1
            for j in range(sy, ey + 1):
                self.grid[sx, j] = 1
                self.grid[ex, j] = 1

    def bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        """خوارزمية بريزنهام لرسم الخطوط واستخدامها في تتبع الأشعة"""
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        points.append((x, y))
        return points

    def calculate_viewshed(self, cx: int, cy: int, radius: int, fov_start: float, fov_end: float) -> set:
        """حساب التغطية المرئية لكاميرا في نقطة معينة مع أخذ العوائق في الحسبان"""
        visible_points = set()
        rays_count = int((fov_end - fov_start) * 2)
        if rays_count <= 0:
            rays_count = 360 * 2
            
        for angle in np.linspace(fov_start, fov_end, rays_count):
            rad = math.radians(angle)
            end_x = int(cx + radius * math.cos(rad))
            end_y = int(cy + radius * math.sin(rad))
            
            end_x = max(0, min(self.width - 1, end_x))
            end_y = max(0, min(self.length - 1, end_y))
            
            line_points = self.bresenham_line(cx, cy, end_x, end_y)
            for px, py in line_points:
                if 0 <= px < self.width and 0 <= py < self.length:
                    visible_points.add((px, py))
                    if self.grid[px, py] == 1:
                        break
        return visible_points

    def generate_candidate_positions(self) -> List[Tuple[int, int]]:
        """توليد مواقع مرشحة للكاميرات في زوايا الغرف وتقاطعات الممرات"""
        candidates = []
        for i in range(1, self.width - 1, 4):
            for j in range(1, self.length - 1, 4):
                if self.grid[i, j] == 0:
                    adjacent_walls = sum([
                        self.grid[i-1, j], self.grid[i+1, j],
                        self.grid[i, j-1], self.grid[i, j+1]
                    ])
                    if adjacent_walls >= 1:
                        candidates.append((i, j))
        return candidates

    def optimize_camera_placement(self, target_coverage: float, camera_type: str) -> None:
        """توزيع الكاميرات باستخدام خوارزمية الغطاء الفئوي الجشعة"""
        candidates = self.generate_candidate_positions()
        
        radius = int(15 / self.grid_size)
        if camera_type == 'dome':
            fov = 360
        elif camera_type == 'bullet':
            fov = 90
        else:
            fov = 180
            
        uncovered = set()
        for i in range(self.width):
            for j in range(self.length):
                if self.grid[i, j] == 0:
                    uncovered.add((i, j))
                    
        total_area = len(uncovered)
        if total_area == 0:
            return
            
        coverage_achieved = 0.0
        
        while coverage_achieved < target_coverage and uncovered:
            best_cam = None
            best_coverage = set()
            best_angle = 0
            
            for cx, cy in candidates:
                for angle in range(0, 360, 45 if fov < 360 else 360):
                    fov_s = angle
                    fov_e = angle + fov
                    visible = self.calculate_viewshed(cx, cy, radius, fov_s, fov_e)
                    valid_visible = visible.intersection(uncovered)
                    
                    if len(valid_visible) > len(best_coverage):
                        best_coverage = valid_visible
                        best_cam = (cx, cy)
                        best_angle = angle
                        
            if not best_cam or len(best_coverage) == 0:
                break
                
            for px, py in best_coverage:
                self.coverage_grid[px, py] = 1
                uncovered.remove((px, py))
                
            self.cameras.append({
                'x': best_cam[0] * self.grid_size,
                'y': best_cam[1] * self.grid_size,
                'type': camera_type,
                'angle': best_angle,
                'fov': fov,
                'radius': radius * self.grid_size
            })
            candidates.remove(best_cam)
            coverage_achieved = ((total_area - len(uncovered)) / total_area) * 100.0

    def place_sensors(self, sensitivity: float) -> None:
        """توزيع المستشعرات في نقاط الدخول والممرات"""
        for room in self.building_data.get('rooms', []):
            rtype = room.get('room_type', '').lower()
            rx = room.get('position_x', 0)
            ry = room.get('position_y', 0)
            rw = room.get('width', 0)
            rl = room.get('length', 0)
            
            if 'corridor' in rtype or 'entry' in rtype or 'hall' in rtype:
                self.sensors.append({
                    'x': rx + rw / 2,
                    'y': ry + rl / 2,
                    'type': 'motion',
                    'sensitivity': sensitivity
                })
                
            if room.get('has_window', False):
                self.sensors.append({
                    'x': rx + rw / 2,
                    'y': ry + rl,
                    'type': 'window_contact'
                })

    def route_cables(self) -> float:
        """توجيه الكابلات وحساب الطول الكلي"""
        total_length = 0.0
        server_x, server_y = 0.0, 0.0
        
        for cam in self.cameras:
            path = []
            cx, cy = cam['x'], cam['y']
            path.append((cx, cy))
            path.append((cx, server_y))
            path.append((server_x, server_y))
            
            length = abs(cx - server_x) + abs(cy - server_y)
            total_length += length
            self.cables.append(path)
            
        for sensor in self.sensors:
            sx, sy = sensor['x'], sensor['y']
            length = abs(sx - server_x) + abs(sy - server_y)
            total_length += length
            
        return total_length

    def assess_security_zones(self) -> Dict[str, Any]:
        """تقييم وتصنيف مناطق الأمان"""
        high_risk = []
        medium_risk = []
        low_risk = []
        
        for room in self.building_data.get('rooms', []):
            rtype = room.get('room_type', '').lower()
            if 'server' in rtype or 'manager' in rtype or 'safe' in rtype:
                high_risk.append(room.get('name', ''))
            elif 'entry' in rtype or 'corridor' in rtype:
                medium_risk.append(room.get('name', ''))
            else:
                low_risk.append(room.get('name', ''))
                
        return {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk
        }
