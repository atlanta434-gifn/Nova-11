import numpy as np

class VentilationEngine:
    """محرك محاكاة التهوية الطبيعية باستخدام طريقة شبكة بولتزمان"""
    
    def __init__(self, building_data, wind_speed, wind_direction, temperature):
        """تهيئة محرك المحاكاة"""
        self.building_data = building_data
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.temperature = temperature
        
        self.nx = 100
        self.ny = 100
        self.tau = 0.6
        
        self.w = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])
        self.cx = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
        self.cy = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])
        
        self.grid = np.zeros((self.nx, self.ny))
        self.obstacle = np.zeros((self.nx, self.ny), dtype=bool)
        self.f = np.zeros((9, self.nx, self.ny))
        self.rho = np.ones((self.nx, self.ny))
        self.u = np.zeros((2, self.nx, self.ny))
        self.pressure = np.zeros((self.nx, self.ny))
        self.ach_results = {}
        self.dead_zones = []
        self.wind_catchers = []
        
    def _map_wind_direction(self):
        """تحويل اتجاه الرياح إلى متجه"""
        dirs = {
            "N": (0, -1),
            "S": (0, 1),
            "E": (1, 0),
            "W": (-1, 0),
            "NE": (1, -1),
            "NW": (-1, -1),
            "SE": (1, 1),
            "SW": (-1, 1)
        }
        return dirs.get(self.wind_direction, (1, 0))

    def setup_domain(self):
        """إعداد النطاق الهندسي للمبنى"""
        if not self.building_data or "rooms" not in self.building_data:
            return
            
        max_x = max([r.get("position_x", 0) + r.get("width", 0) for r in self.building_data["rooms"]] + [1])
        max_y = max([r.get("position_y", 0) + r.get("length", 0) for r in self.building_data["rooms"]] + [1])
        
        scale_x = self.nx / (max_x * 1.5)
        scale_y = self.ny / (max_y * 1.5)
        
        for room in self.building_data["rooms"]:
            rx = int((room.get("position_x", 0) + max_x * 0.25) * scale_x)
            ry = int((room.get("position_y", 0) + max_y * 0.25) * scale_y)
            rw = int(room.get("width", 1) * scale_x)
            rh = int(room.get("length", 1) * scale_y)
            
            rx = max(1, min(rx, self.nx - 2))
            ry = max(1, min(ry, self.ny - 2))
            rw = max(1, min(rw, self.nx - rx - 1))
            rh = max(1, min(rh, self.ny - ry - 1))
            
            self.obstacle[rx:rx+rw, ry] = True
            self.obstacle[rx:rx+rw, ry+rh] = True
            self.obstacle[rx, ry:ry+rh] = True
            self.obstacle[rx+rw, ry:ry+rh] = True
            
            if room.get("has_window", False):
                self.obstacle[rx+rw//3:rx+2*rw//3, ry] = False
                self.obstacle[rx+rw//3:rx+2*rw//3, ry+rh] = False

        vx, vy = self._map_wind_direction()
        vx = vx * self.wind_speed * 0.05
        vy = vy * self.wind_speed * 0.05
        
        for i in range(9):
            cu = 3 * (self.cx[i] * vx + self.cy[i] * vy)
            self.f[i, :, :] = self.rho * self.w[i] * (1 + cu + 0.5 * cu**2 - 1.5 * (vx**2 + vy**2))

    def run_simulation(self, steps=100):
        """تنفيذ المحاكاة"""
        vx, vy = self._map_wind_direction()
        v0_x = vx * self.wind_speed * 0.05
        v0_y = vy * self.wind_speed * 0.05
        
        for _ in range(steps):
            for i in range(9):
                self.f[i, :, :] = np.roll(np.roll(self.f[i, :, :], self.cx[i], axis=0), self.cy[i], axis=1)
                
            bndryF = self.f[:, self.obstacle]
            bndryF = bndryF[[0, 3, 4, 1, 2, 7, 8, 5, 6], :]
            
            if vx > 0:
                self.f[[1, 5, 8], 0, :] = self.w[[1, 5, 8]][:, np.newaxis] * (1 + 3*v0_x + 4.5*v0_x**2 - 1.5*v0_x**2)
            elif vx < 0:
                self.f[[3, 6, 7], -1, :] = self.w[[3, 6, 7]][:, np.newaxis] * (1 - 3*v0_x + 4.5*v0_x**2 - 1.5*v0_x**2)
                
            if vy > 0:
                self.f[[2, 5, 6], :, 0] = self.w[[2, 5, 6]][:, np.newaxis] * (1 + 3*v0_y + 4.5*v0_y**2 - 1.5*v0_y**2)
            elif vy < 0:
                self.f[[4, 7, 8], :, -1] = self.w[[4, 7, 8]][:, np.newaxis] * (1 - 3*v0_y + 4.5*v0_y**2 - 1.5*v0_y**2)
                
            self.rho = np.sum(self.f, axis=0)
            self.u[0] = np.sum(self.f * self.cx[:, np.newaxis, np.newaxis], axis=0) / self.rho
            self.u[1] = np.sum(self.f * self.cy[:, np.newaxis, np.newaxis], axis=0) / self.rho
            
            self.f[:, self.obstacle] = bndryF
            self.u[:, self.obstacle] = 0
            
            feq = np.zeros((9, self.nx, self.ny))
            u2 = self.u[0]**2 + self.u[1]**2
            for i in range(9):
                cu = 3 * (self.cx[i] * self.u[0] + self.cy[i] * self.u[1])
                feq[i] = self.rho * self.w[i] * (1 + cu + 0.5 * cu**2 - 1.5 * u2)
                
            self.f += -(1.0 / self.tau) * (self.f - feq)
            
        self.pressure = self.rho / 3.0
        self._calculate_metrics()

    def _calculate_metrics(self):
        """حساب معايير التهوية لكل غرفة"""
        velocity_mag = np.sqrt(self.u[0]**2 + self.u[1]**2)
        
        if not self.building_data or "rooms" not in self.building_data:
            return
            
        max_x = max([r.get("position_x", 0) + r.get("width", 0) for r in self.building_data["rooms"]] + [1])
        max_y = max([r.get("position_y", 0) + r.get("length", 0) for r in self.building_data["rooms"]] + [1])
        scale_x = self.nx / (max_x * 1.5)
        scale_y = self.ny / (max_y * 1.5)
        
        for room in self.building_data["rooms"]:
            rx = int((room.get("position_x", 0) + max_x * 0.25) * scale_x)
            ry = int((room.get("position_y", 0) + max_y * 0.25) * scale_y)
            rw = int(room.get("width", 1) * scale_x)
            rh = int(room.get("length", 1) * scale_y)
            
            rx = max(1, min(rx, self.nx - 2))
            ry = max(1, min(ry, self.ny - 2))
            rw = max(1, min(rw, self.nx - rx - 1))
            rh = max(1, min(rh, self.ny - ry - 1))
            
            room_vel = velocity_mag[rx:rx+rw, ry:ry+rh]
            room_p = self.pressure[rx:rx+rw, ry:ry+rh]
            
            avg_vel = np.mean(room_vel) if room_vel.size > 0 else 0.0
            avg_p = np.mean(room_p) if room_p.size > 0 else 0.0
            
            ach = avg_vel * 3600 * 0.1
            
            status = "جيد"
            color = "#3FB950"
            if ach < 2:
                status = "سيء"
                color = "#F85149"
            elif ach < 4:
                status = "متوسط"
                color = "#D29922"
                
            name = room.get("name", "غرفة")
            self.ach_results[name] = {
                "ach": ach,
                "status": status,
                "color": color,
                "pressure": avg_p,
                "center": (rx + rw/2, ry + rh/2)
            }
            
            if ach < 2:
                self.dead_zones.append({
                    "x": rx + rw/2,
                    "y": ry + rh/2,
                    "room": name
                })
                
            if avg_p > 0.34:
                self.wind_catchers.append({
                    "x": rx + rw/2,
                    "y": ry + rh/2,
                    "room": name
                })

    def get_results(self):
        """إرجاع نتائج المحاكاة"""
        return {
            "u": self.u,
            "pressure": self.pressure,
            "obstacle": self.obstacle,
            "ach": self.ach_results,
            "dead_zones": self.dead_zones,
            "wind_catchers": self.wind_catchers
        }
