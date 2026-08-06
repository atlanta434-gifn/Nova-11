import numpy as np
from typing import Dict, Any, List


class ThermalSimulator:
    """محاكي حراري مبسط لحساب الأحمال الحرارية وانتقال الحرارة"""

    def __init__(self):
        self.grid_resolution = 0.5
        self.outdoor_temp = 45.0
        self.indoor_target = 24.0
        self.u_values = {
            "wall_ext": 1.2,
            "wall_int": 2.5,
            "window": 3.0,
            "roof": 0.8,
        }

    def simulate(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """تشغيل محاكاة حرارية بسيطة (Steady-State)"""
        pw = building_data.get("plot_width", 20)
        pl = building_data.get("plot_length", 25)

        grid_w = int(pw / self.grid_resolution)
        grid_h = int(pl / self.grid_resolution)

        temp_grid = np.ones((grid_h, grid_w)) * self.outdoor_temp

        rooms = building_data.get("rooms", [])
        total_cooling_load = 0.0
        room_loads = []

        for room in rooms:
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 4)
            rl = room.get("length", 4)

            x_start = max(0, int(px / self.grid_resolution))
            y_start = max(0, int(py / self.grid_resolution))
            x_end = min(grid_w, int((px + rw) / self.grid_resolution))
            y_end = min(grid_h, int((py + rl) / self.grid_resolution))

            temp_grid[y_start:y_end, x_start:x_end] = self.indoor_target

            area = rw * rl
            perimeter = 2 * (rw + rl)
            delta_t = self.outdoor_temp - self.indoor_target

            wall_load = perimeter * 3.0 * self.u_values["wall_ext"] * delta_t
            roof_load = area * self.u_values["roof"] * delta_t
            internal_load = area * 15.0

            room_load = wall_load + roof_load + internal_load
            total_cooling_load += room_load

            room_loads.append({
                "name": room.get("name", "Room"),
                "cooling_load_w": room_load,
                "cooling_load_ton": room_load / 3516.85
            })

        from scipy.ndimage import gaussian_filter
        temp_grid = gaussian_filter(temp_grid, sigma=1.5)

        return {
            "temp_grid": temp_grid,
            "grid_extent": [0, pw, 0, pl],
            "total_cooling_load_w": total_cooling_load,
            "total_cooling_load_ton": total_cooling_load / 3516.85,
            "room_loads": room_loads,
            "outdoor_temp": self.outdoor_temp,
            "indoor_target": self.indoor_target,
        }
