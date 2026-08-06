import numpy as np
from typing import Dict, Any


class AirflowSimulator:
    """محاكي تدفق الهواء ثنائي الأبعاد (مبسط)"""

    def __init__(self):
        self.grid_resolution = 0.5
        self.wind_speed = 5.0
        self.wind_angle = 45.0

    def simulate(self, building_data: Dict[str, Any]) -> Dict[str, Any]:
        """توليد حقول متجهية لتدفق الهواء (استخدام دالة الجهد)"""
        pw = building_data.get("plot_width", 20)
        pl = building_data.get("plot_length", 25)

        grid_w = int(pw / self.grid_resolution)
        grid_h = int(pl / self.grid_resolution)

        x = np.linspace(0, pw, grid_w)
        y = np.linspace(0, pl, grid_h)
        X, Y = np.meshgrid(x, y)

        angle_rad = np.radians(self.wind_angle)
        u_base = self.wind_speed * np.cos(angle_rad)
        v_base = self.wind_speed * np.sin(angle_rad)

        U = np.ones_like(X) * u_base
        V = np.ones_like(Y) * v_base
        Speed = np.sqrt(U**2 + V**2)

        rooms = building_data.get("rooms", [])
        mask = np.zeros_like(X, dtype=bool)

        for room in rooms:
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 4)
            rl = room.get("length", 4)

            x_mask = (X >= px) & (X <= px + rw)
            y_mask = (Y >= py) & (Y <= py + rl)
            mask |= (x_mask & y_mask)

        U[mask] = 0.1
        V[mask] = 0.1
        Speed[mask] = np.sqrt(U[mask]**2 + V[mask]**2)

        from scipy.ndimage import gaussian_filter
        U = gaussian_filter(U, sigma=1.0)
        V = gaussian_filter(V, sigma=1.0)
        Speed = np.sqrt(U**2 + V**2)

        return {
            "X": X,
            "Y": Y,
            "U": U,
            "V": V,
            "Speed": Speed,
            "wind_speed": self.wind_speed,
            "wind_angle": self.wind_angle,
        }
