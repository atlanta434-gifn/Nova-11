import numpy as np
from typing import Dict, Any, List, Tuple
import math

class StructuralEngine:
    """محرك التحليل الإنشائي والتصميم"""
    
    def __init__(self, building_data: Dict[str, Any], soil_capacity: float, concrete_grade: str, steel_grade: str, seismic_zone: int):
        """تهيئة محرك التحليل"""
        self.building_data = building_data
        self.soil_capacity = soil_capacity
        self.concrete_grade = float(concrete_grade.replace("C", ""))
        self.steel_grade = float(steel_grade)
        self.seismic_zone = seismic_zone
        self.floors = self.building_data.get("total_floors", 1)
        self.results: Dict[str, Any] = {}
        self.columns: List[Dict[str, Any]] = []
        self.beams: List[Dict[str, Any]] = []
        self.slabs: List[Dict[str, Any]] = []
        
    def analyze(self) -> Dict[str, Any]:
        """تنفيذ عملية التحليل الشاملة"""
        self._extract_geometry()
        self._calculate_loads()
        self._analyze_slabs()
        self._analyze_beams()
        self._analyze_columns()
        self._analyze_foundations()
        self._calculate_lateral_loads()
        self._calculate_quantities()
        self.results["columns"] = self.columns
        self.results["beams"] = self.beams
        self.results["slabs"] = self.slabs
        return self.results
        
    def _extract_geometry(self):
        """استخراج الشبكة الإنشائية من الغرف"""
        rooms = self.building_data.get("rooms", [])
        pts = set()
        for r in rooms:
            x, y = r["position_x"], r["position_y"]
            w, l = r["width"], r["length"]
            pts.add((round(x, 2), round(y, 2)))
            pts.add((round(x+w, 2), round(y, 2)))
            pts.add((round(x, 2), round(y+l, 2)))
            pts.add((round(x+w, 2), round(y+l, 2)))
        
        nodes = list(pts)
        for idx, (nx, ny) in enumerate(nodes):
            self.columns.append({
                "id": idx + 1,
                "x": nx,
                "y": ny,
                "trib_area": 0.0,
                "load_dl": 0.0,
                "load_ll": 0.0
            })
            
        for r in rooms:
            x, y = r["position_x"], r["position_y"]
            w, l = r["width"], r["length"]
            self.slabs.append({
                "name": r.get("name", "غرفة"),
                "x": x, "y": y, "w": w, "l": l,
                "type": r.get("room_type", "عام")
            })
            
        for c1 in self.columns:
            for c2 in self.columns:
                if c1["id"] >= c2["id"]:
                    continue
                dx = abs(c1["x"] - c2["x"])
                dy = abs(c1["y"] - c2["y"])
                if (dx < 0.1 and 1.5 < dy < 8.0) or (dy < 0.1 and 1.5 < dx < 8.0):
                    self.beams.append({
                        "id": len(self.beams) + 1,
                        "n1": c1,
                        "n2": c2,
                        "length": math.hypot(dx, dy)
                    })

    def _calculate_loads(self):
        """حساب الأحمال الميتة والحية"""
        for s in self.slabs:
            s["dl"] = 4.5
            s["ll"] = 3.0 if "عام" not in s["type"] else 2.0
            s["wu"] = 1.2 * s["dl"] + 1.6 * s["ll"]

    def _analyze_slabs(self):
        """تصميم البلاطات وحساب السماكة"""
        for s in self.slabs:
            ratio = max(s["w"], s["l"]) / min(s["w"], s["l"])
            if ratio > 2.0:
                s["slab_type"] = "One-way"
                s["thickness"] = max(150, min(s["w"], s["l"]) * 1000 / 24)
            else:
                s["slab_type"] = "Two-way"
                s["thickness"] = max(150, (s["w"] + s["l"]) * 1000 / 90)

    def _analyze_beams(self):
        """تصميم الجيزان وحساب الأبعاد"""
        for b in self.beams:
            L = b["length"]
            b["depth"] = max(300, L * 1000 / 16)
            b["width"] = max(200, b["depth"] / 2)
            b["load"] = 15.0 
            b["moment"] = (b["load"] * L**2) / 8
            
            E = 4700 * math.sqrt(self.concrete_grade)
            I = (b["width"] * (b["depth"]**3)) / 12
            matrix_k = np.array([
                [12, 6*L, -12, 6*L],
                [6*L, 4*L**2, -6*L, 2*L**2],
                [-12, -6*L, 12, -6*L],
                [6*L, 2*L**2, -6*L, 4*L**2]
            ]) * (E * I / L**3)
            b["stiffness"] = matrix_k.tolist()
            b["stress_ratio"] = min(1.0, b["moment"] / (b["width"] * b["depth"] * self.concrete_grade / 1000))

    def _analyze_columns(self):
        """تصميم الأعمدة وحساب القطاعات"""
        for c in self.columns:
            c["trib_area"] = 12.0
            c["total_wu"] = c["trib_area"] * 10.0 * self.floors
            req_area = (c["total_wu"] * 1000) / (0.4 * self.concrete_grade)
            side = math.sqrt(req_area)
            c["size"] = max(200, math.ceil(side / 50) * 50)
            c["stress_ratio"] = min(1.0, req_area / (c["size"]**2))

    def _analyze_foundations(self):
        """تصميم القواعد وحساب الأبعاد"""
        for c in self.columns:
            service_load = c["trib_area"] * 7.5 * self.floors
            req_area = service_load / self.soil_capacity
            side = math.sqrt(req_area)
            c["footing_size"] = max(1.0, math.ceil(side / 0.1) * 0.1)

    def _calculate_lateral_loads(self):
        """حساب الأحمال الزلزالية والرياح"""
        w_total = sum(c["total_wu"] for c in self.columns)
        cs = 0.05 * self.seismic_zone
        self.results["base_shear"] = cs * w_total
        self.results["wind_pressure"] = 1.2 * self.floors

    def _calculate_quantities(self):
        """حساب الكميات الإجمالية"""
        v_concrete = sum((c["size"]/1000)**2 * 3.0 for c in self.columns) * self.floors
        v_concrete += sum((b["width"]/1000)*(b["depth"]/1000)*b["length"] for b in self.beams) * self.floors
        self.results["total_concrete"] = v_concrete
        self.results["total_steel"] = v_concrete * 120
