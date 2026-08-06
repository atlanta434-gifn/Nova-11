import math
from collections import defaultdict
import heapq
from typing import Dict, List, Any, Tuple

class PlumbingEngine:
    """محرك الحسابات لتمديدات المياه والصرف الصحي"""

    def __init__(self, building_data: Dict[str, Any], params: Dict[str, Any]):
        self.building_data = building_data
        self.params = params
        self.nodes = []
        self.edges = []
        self.cold_water_network = []
        self.hot_water_network = []
        self.drainage_network = []
        self.results = {}
        
    def generate_networks(self):
        """توليد جميع الشبكات بناءً على المعطيات"""
        self._build_graph()
        self._route_cold_water()
        self._route_hot_water()
        self._route_drainage()
        self._calculate_pipe_sizes()
        self._calculate_pressure()
        self._design_rainwater_harvesting()
        self._compile_results()
        return self.results

    def _build_graph(self):
        """بناء المخطط الشبكي للمبنى"""
        main_entry = (0.0, 0.0)
        self.nodes.append({"id": "main_entry", "pos": main_entry, "type": "entry"})
        
        heater_loc = self.params.get("heater_location", "Main")
        
        idx = 0
        for room in self.building_data.get("rooms", []):
            rx, ry = room.get("position_x", 0.0), room.get("position_y", 0.0)
            cx = rx + room.get("width", 0.0) / 2
            cy = ry + room.get("length", 0.0) / 2
            rtype = room.get("room_type", "").lower()
            
            node_id = f"room_{idx}"
            node_type = "wet" if rtype in ["bathroom", "kitchen", "حمام", "مطبخ"] else "standard"
            
            self.nodes.append({"id": node_id, "pos": (cx, cy), "type": node_type, "room": room})
            
            if rtype == heater_loc.lower() or heater_loc == "Main":
                if not any(n["id"] == "heater" for n in self.nodes):
                    self.nodes.append({"id": "heater", "pos": (cx, cy), "type": "heater"})
            idx += 1
            
        for i, n1 in enumerate(self.nodes):
            for j, n2 in enumerate(self.nodes):
                if i < j:
                    dist = math.hypot(n1["pos"][0] - n2["pos"][0], n1["pos"][1] - n2["pos"][1])
                    self.edges.append((dist, n1["id"], n2["id"]))

    def _route_cold_water(self):
        """خوارزمية الشجرة الممتدة الصغرى لشبكة المياه الباردة"""
        parent = {}
        def find(i):
            if parent[i] == i:
                return i
            parent[i] = find(parent[i])
            return parent[i]
            
        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j
                
        for n in self.nodes:
            parent[n["id"]] = n["id"]
            
        sorted_edges = sorted(self.edges, key=lambda x: x[0])
        wet_nodes = [n["id"] for n in self.nodes if n["type"] in ["wet", "heater"]]
        wet_nodes.append("main_entry")
        
        for weight, u, v in sorted_edges:
            if u in wet_nodes and v in wet_nodes:
                if find(u) != find(v):
                    union(u, v)
                    self.cold_water_network.append({"u": u, "v": v, "length": weight, "type": "cold"})

    def _route_hot_water(self):
        """خوارزمية ديكسترا لشبكة المياه الساخنة"""
        graph = defaultdict(list)
        for weight, u, v in self.edges:
            graph[u].append((weight, v))
            graph[v].append((weight, u))
            
        heater_nodes = [n["id"] for n in self.nodes if n["type"] == "heater"]
        if not heater_nodes:
            return
        start = heater_nodes[0]
        
        distances = {n["id"]: float('infinity') for n in self.nodes}
        distances[start] = 0
        pq = [(0, start)]
        previous = {n["id"]: None for n in self.nodes}
        
        while pq:
            current_dist, current_vertex = heapq.heappop(pq)
            if current_dist > distances[current_vertex]:
                continue
            for weight, neighbor in graph[current_vertex]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_vertex
                    heapq.heappush(pq, (distance, neighbor))
                    
        wet_nodes = [n["id"] for n in self.nodes if n["type"] == "wet"]
        for target in wet_nodes:
            curr = target
            while previous[curr]:
                prev = previous[curr]
                dist = math.hypot(
                    next(n["pos"][0] for n in self.nodes if n["id"] == curr) - next(n["pos"][0] for n in self.nodes if n["id"] == prev),
                    next(n["pos"][1] for n in self.nodes if n["id"] == curr) - next(n["pos"][1] for n in self.nodes if n["id"] == prev)
                )
                self.hot_water_network.append({"u": curr, "v": prev, "length": dist, "type": "hot"})
                curr = prev

    def _route_drainage(self):
        """توجيه شبكة الصرف الصحي مع حساب الميول"""
        for n in self.nodes:
            if n["type"] == "wet":
                dist = math.hypot(n["pos"][0], n["pos"][1])
                slope_drop = dist * 0.02
                self.drainage_network.append({
                    "u": n["id"], 
                    "v": "main_entry", 
                    "length": dist, 
                    "type": "drainage",
                    "slope_drop": slope_drop
                })

    def _calculate_pipe_sizes(self):
        """طريقة هانتر لحساب أقطار الأنابيب"""
        for edge in self.cold_water_network + self.hot_water_network + self.drainage_network:
            fixture_units = 2.0 
            flow_rate = fixture_units * 0.3 
            diameter = math.sqrt((4 * flow_rate) / (math.pi * 1.5)) * 1000 
            edge["diameter"] = max(15.0, diameter)
            if edge["type"] == "drainage":
                edge["diameter"] = max(100.0, diameter * 3)

    def _calculate_pressure(self):
        """معادلة هازن-ويليامز لحساب هبوط الضغط"""
        material = self.params.get("material", "PVC")
        c_factor = 150 if material == "PVC" else (130 if material == "Copper" else 140)
        
        for edge in self.cold_water_network:
            q = 0.5 
            d = edge["diameter"] / 1000.0 
            if d > 0:
                hf = 10.67 * (q ** 1.852) / ((c_factor ** 1.852) * (d ** 4.8704)) * edge["length"]
                edge["pressure_drop"] = hf

    def _design_rainwater_harvesting(self):
        """تصميم نظام حصاد مياه الأمطار"""
        roof_area = self.building_data.get("plot_width", 10.0) * self.building_data.get("plot_length", 10.0)
        rainfall_mm = 300 
        collection_volume = roof_area * (rainfall_mm / 1000) * 0.8 
        self.results["rainwater_volume"] = collection_volume
        self.results["tank_size"] = collection_volume * 1.2

    def _compile_results(self):
        """تجميع النتائج النهائية"""
        cold_len = sum(e["length"] for e in self.cold_water_network)
        hot_len = sum(e["length"] for e in self.hot_water_network)
        drain_len = sum(e["length"] for e in self.drainage_network)
        
        self.results.update({
            "nodes": self.nodes,
            "cold_network": self.cold_water_network,
            "hot_network": self.hot_water_network,
            "drain_network": self.drainage_network,
            "total_cold_length": cold_len,
            "total_hot_length": hot_len,
            "total_drain_length": drain_len,
            "estimated_consumption": self.params.get("occupants", 4) * 150,
            "pump_power_kw": 0.75 * math.ceil((cold_len + hot_len) / 50)
        })
