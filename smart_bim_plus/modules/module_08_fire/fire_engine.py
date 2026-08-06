import numpy as np
import heapq
import math

class FireSafetyEngine:
    """محرك الحسابات الخاص بأنظمة الإطفاء والسلامة"""
    
    def __init__(self, building_data, hazard_class, occupants_per_room, num_exits):
        self.building_data = building_data
        self.hazard_class = hazard_class
        self.occupants_per_room = occupants_per_room
        self.num_exits = num_exits
        
        self.sprinkler_radius = {"light": 4.6, "ordinary": 3.7, "extra": 3.0}.get(hazard_class, 3.7)
        self.extinguisher_spacing = 15.0
        self.detector_spacing = 9.1
        
        self.rooms = building_data.get("rooms", [])
        self._calculate_bounds()
        
    def _calculate_bounds(self):
        """حساب حدود المبنى"""
        if not self.rooms:
            self.min_x, self.min_y, self.max_x, self.max_y = 0, 0, 10, 10
            return
            
        min_x = min(r.get("position_x", 0) for r in self.rooms)
        min_y = min(r.get("position_y", 0) for r in self.rooms)
        max_x = max(r.get("position_x", 0) + r.get("width", 0) for r in self.rooms)
        max_y = max(r.get("position_y", 0) + r.get("length", 0) for r in self.rooms)
        
        self.min_x, self.min_y, self.max_x, self.max_y = min_x, min_y, max_x, max_y
        
    def generate_system(self):
        """توليد جميع عناصر النظام"""
        exits = self._place_exits()
        sprinklers = self._distribute_sprinklers()
        extinguishers = self._distribute_extinguishers()
        detectors = self._distribute_detectors()
        pull_stations = exits.copy()
        emergency_lights = self._distribute_emergency_lights(exits)
        
        routes, times = self._calculate_evacuation(exits)
        
        return {
            "exits": exits,
            "sprinklers": sprinklers,
            "extinguishers": extinguishers,
            "detectors": detectors,
            "pull_stations": pull_stations,
            "emergency_lights": emergency_lights,
            "routes": routes,
            "times": times
        }

    def _place_exits(self):
        """توزيع مخارج الطوارئ"""
        exits = []
        if self.num_exits >= 1:
            exits.append((self.max_x, self.min_y + (self.max_y - self.min_y)/2))
        if self.num_exits >= 2:
            exits.append((self.min_x, self.min_y + (self.max_y - self.min_y)/2))
        if self.num_exits >= 3:
            exits.append((self.min_x + (self.max_x - self.min_x)/2, self.max_y))
        if self.num_exits >= 4:
            exits.append((self.min_x + (self.max_x - self.min_x)/2, self.min_y))
        return exits
        
    def _distribute_sprinklers(self):
        """توزيع مرشات المياه باستخدام خوارزمية التغطية"""
        sprinklers = []
        r = self.sprinkler_radius
        for room in self.rooms:
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            w, l = room.get("width", 5), room.get("length", 5)
            
            x_steps = max(1, math.ceil(w / (r * 1.5)))
            y_steps = max(1, math.ceil(l / (r * 1.5)))
            
            x_spacing = w / x_steps
            y_spacing = l / y_steps
            
            for i in range(x_steps):
                for j in range(y_steps):
                    sx = px + (i + 0.5) * x_spacing
                    sy = py + (j + 0.5) * y_spacing
                    sprinklers.append((sx, sy))
        return sprinklers
        
    def _distribute_extinguishers(self):
        """توزيع طفايات الحريق"""
        extinguishers = []
        for room in self.rooms:
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            extinguishers.append((px + 0.5, py + 0.5))
        return extinguishers

    def _distribute_detectors(self):
        """توزيع كواشف الدخان"""
        detectors = []
        for room in self.rooms:
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            w, l = room.get("width", 5), room.get("length", 5)
            detectors.append((px + w/2, py + l/2))
        return detectors
        
    def _distribute_emergency_lights(self, exits):
        """توزيع إضاءة الطوارئ"""
        return exits.copy()
        
    def _calculate_evacuation(self, exits):
        """حساب مسارات ووقت الإخلاء باستخدام A*"""
        routes = {}
        times = {}
        speed = 1.2
        
        for room in self.rooms:
            name = room.get("name", "غرفة")
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            w, l = room.get("width", 5), room.get("length", 5)
            start_x, start_y = px + w/2, py + l/2
            
            best_exit = None
            min_dist = float('inf')
            for ex, ey in exits:
                dist = math.hypot(ex - start_x, ey - start_y)
                if dist < min_dist:
                    min_dist = dist
                    best_exit = (ex, ey)
                    
            if best_exit:
                routes[name] = [(start_x, start_y), best_exit]
                time_sec = (min_dist / speed) + (self.occupants_per_room * 1.5)
                times[name] = time_sec
                
        return routes, times
