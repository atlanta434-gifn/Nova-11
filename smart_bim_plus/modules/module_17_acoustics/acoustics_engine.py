import numpy as np
import math
from typing import Dict, Any, List, Tuple

class AcousticsEngine:
    """محرك الحسابات الصوتية"""
    
    def __init__(self):
        """تهيئة المحرك"""
        self.absorption_coeffs = {
            "خرسانة": 0.02,
            "جدران جافة": 0.05,
            "سجاد": 0.3,
            "ألواح صوتية": 0.8,
            "خشب": 0.1
        }
        self.stc_ratings = {
            "خرسانة": 55,
            "جدران جافة": 35,
            "ألواح صوتية": 45,
            "خشب": 40
        }

    def calculate_rt60(self, width: float, length: float, height: float, 
                       wall_mat: str, floor_mat: str, ceil_mat: str) -> float:
        """حساب زمن الرنين"""
        v = width * length * height
        wall_area = 2 * height * (width + length)
        floor_area = width * length
        ceil_area = width * length
        
        a_wall = wall_area * self.absorption_coeffs.get(wall_mat, 0.05)
        a_floor = floor_area * self.absorption_coeffs.get(floor_mat, 0.05)
        a_ceil = ceil_area * self.absorption_coeffs.get(ceil_mat, 0.05)
        
        a_total = a_wall + a_floor + a_ceil
        if a_total == 0:
            return 0.0
            
        rt60 = 0.161 * v / a_total
        return rt60

    def calculate_spl_grid(self, width: float, length: float, source_pos: tuple, resolution: float = 0.5) -> tuple:
        """حساب توزيع ضغط الصوت"""
        x_steps = max(2, int(width / resolution))
        y_steps = max(2, int(length / resolution))
        
        x_coords = np.linspace(0, width, x_steps)
        y_coords = np.linspace(0, length, y_steps)
        xx, yy = np.meshgrid(x_coords, y_coords)
        
        dist = np.sqrt((xx - source_pos[0])**2 + (yy - source_pos[1])**2)
        dist = np.maximum(dist, 0.1)
        
        spl = 100 - 20 * np.log10(dist)
        spl = np.clip(spl, 40, 110)
        
        return spl, x_coords, y_coords

    def ray_tracing(self, width: float, length: float, source_pos: tuple, 
                    wall_mat: str, num_rays: int = 360, max_reflections: int = 5) -> list:
        """تتبع مسارات الأشعة الصوتية"""
        rays = []
        alpha = self.absorption_coeffs.get(wall_mat, 0.05)
        
        for i in range(num_rays):
            angle = i * (2 * math.pi / num_rays)
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            x, y = source_pos
            energy = 1.0
            path = [(x, y)]
            
            for _ in range(max_reflections):
                t_x, t_y = float('inf'), float('inf')
                if dx > 1e-6:
                    t_x = (width - x) / dx
                elif dx < -1e-6:
                    t_x = -x / dx
                    
                if dy > 1e-6:
                    t_y = (length - y) / dy
                elif dy < -1e-6:
                    t_y = -y / dy
                    
                t = min(t_x, t_y)
                if t == float('inf') or t == 0:
                    break
                    
                x += dx * t
                y += dy * t
                path.append((x, y))
                
                if t == t_x:
                    dx = -dx
                else:
                    dy = -dy
                    
                energy *= (1 - alpha)
                if energy < 0.01:
                    break
                    
            rays.append(path)
            
        return rays

    def optimize_speaker_placement(self, width: float, length: float, system_type: str) -> list:
        """تحسين أماكن السماعات"""
        center_x, center_y = width / 2, length / 2
        listener_pos = (center_x, center_y - length * 0.1)
        
        speakers = []
        radius = min(width, length) * 0.4
        
        if system_type in ["5.1", "7.1", "Atmos"]:
            speakers.append((center_x, listener_pos[1] + radius, "Center"))
            speakers.append((center_x - radius * 0.8, listener_pos[1] + radius * 0.8, "Front L"))
            speakers.append((center_x + radius * 0.8, listener_pos[1] + radius * 0.8, "Front R"))
            speakers.append((center_x - radius, listener_pos[1] - radius * 0.2, "Surround L"))
            speakers.append((center_x + radius, listener_pos[1] - radius * 0.2, "Surround R"))
            speakers.append((center_x + radius * 0.5, listener_pos[1] + radius * 0.5, "Subwoofer"))
            
        if system_type in ["7.1", "Atmos"]:
            speakers.append((center_x - radius * 0.6, listener_pos[1] - radius * 0.8, "Back L"))
            speakers.append((center_x + radius * 0.6, listener_pos[1] - radius * 0.8, "Back R"))
            
        if system_type == "Atmos":
            speakers.append((center_x - radius * 0.4, listener_pos[1] + radius * 0.2, "Top Front L"))
            speakers.append((center_x + radius * 0.4, listener_pos[1] + radius * 0.2, "Top Front R"))
            speakers.append((center_x - radius * 0.4, listener_pos[1] - radius * 0.2, "Top Rear L"))
            speakers.append((center_x + radius * 0.4, listener_pos[1] - radius * 0.2, "Top Rear R"))
            
        return speakers
