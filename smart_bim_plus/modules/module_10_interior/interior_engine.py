import numpy as np
from shapely.geometry import Polygon, box, LineString
from typing import Dict, List, Any, Tuple, Optional
import math

class InteriorEngine:
    """محرك التصميم الداخلي لتوزيع الأثاث وتحليل الفراغات"""

    def __init__(self):
        """تهيئة محرك التصميم الداخلي"""
        self.clearance = 0.6
        self.catalogs = {
            "bedroom": [
                {"name": "سرير مزدوج", "w": 2.0, "l": 2.0, "color": "#58A6FF", "req_wall": True},
                {"name": "خزانة ملابس", "w": 2.0, "l": 0.6, "color": "#3FB950", "req_wall": True},
                {"name": "طاولة جانبية", "w": 0.5, "l": 0.5, "color": "#D29922", "req_wall": False},
                {"name": "مكتب", "w": 1.2, "l": 0.6, "color": "#F85149", "req_wall": True}
            ],
            "kitchen": [
                {"name": "حوض غسيل", "w": 0.9, "l": 0.6, "color": "#58A6FF", "req_wall": True},
                {"name": "موقد", "w": 0.9, "l": 0.6, "color": "#F85149", "req_wall": True},
                {"name": "ثلاجة", "w": 0.9, "l": 0.8, "color": "#D29922", "req_wall": True}
            ],
            "bathroom": [
                {"name": "مرحاض", "w": 0.5, "l": 0.7, "color": "#F85149", "req_wall": True},
                {"name": "مغسلة", "w": 0.6, "l": 0.5, "color": "#58A6FF", "req_wall": True},
                {"name": "حوض استحمام", "w": 1.7, "l": 0.8, "color": "#3FB950", "req_wall": True}
            ],
            "living": [
                {"name": "أريكة رئيسية", "w": 2.2, "l": 0.9, "color": "#58A6FF", "req_wall": False},
                {"name": "تلفاز", "w": 1.5, "l": 0.3, "color": "#F85149", "req_wall": True},
                {"name": "طاولة قهوة", "w": 1.0, "l": 0.6, "color": "#D29922", "req_wall": False}
            ]
        }

    def analyze_space_syntax(self, rooms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل الترابط الفراغي"""
        n = len(rooms)
        if n == 0:
            return {}
        
        centers = []
        for r in rooms:
            cx = r.get("position_x", 0) + r.get("width", 0) / 2
            cy = r.get("position_y", 0) + r.get("length", 0) / 2
            centers.append((cx, cy))
            
        adj_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                dist = math.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1])
                threshold = (max(rooms[i].get("width", 0), rooms[i].get("length", 0)) + 
                             max(rooms[j].get("width", 0), rooms[j].get("length", 0)))
                if dist < threshold * 1.5:
                    adj_matrix[i][j] = 1
                    adj_matrix[j][i] = 1
                    
        connectivity = np.sum(adj_matrix, axis=1)
        integration = np.zeros(n)
        for i in range(n):
            integration[i] = (connectivity[i] / (n - 1)) if n > 1 else 1.0
            
        return {
            rooms[i]["name"]: {
                "connectivity": connectivity[i],
                "integration": integration[i]
            } for i in range(n)
        }

    def recommend_materials(self, room_type: str, style: str, budget: str) -> Dict[str, str]:
        """توصية مواد التشطيب"""
        recs = {
            "floor": "سيراميك",
            "wall": "دهان بلاستيك",
            "ceiling": "جبس بورد"
        }
        
        if style == "كلاسيكي":
            recs["floor"] = "رخام" if budget == "فاخر" else "بورسلان"
            recs["wall"] = "ورق حائط"
        elif style == "حديث":
            recs["floor"] = "خشب باركيه" if budget != "اقتصادي" else "فينيل"
            recs["wall"] = "دهان مطفي"
            recs["ceiling"] = "سقف مشدود"
        elif style == "عربي":
            recs["floor"] = "بلاط مزخرف"
            recs["wall"] = "زخارف جصية"
            recs["ceiling"] = "خشب محفور"
            
        return recs

    def place_furniture(self, rooms: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """توزيع الأثاث في الغرف"""
        layouts = {}
        for room in rooms:
            room_type = str(room.get("room_type", "")).lower()
            rtype_mapped = self._map_room_type(room_type)
            items = self.catalogs.get(rtype_mapped, self.catalogs["living"])
            
            rx = room.get("position_x", 0.0)
            ry = room.get("position_y", 0.0)
            rw = room.get("width", 3.0)
            rl = room.get("length", 3.0)
            
            placed = []
            occupied_polygons = []
            
            for item in items:
                pos = self._find_position(rx, ry, rw, rl, item, occupied_polygons)
                if pos:
                    x, y, w, l = pos
                    poly = box(x - self.clearance/2, y - self.clearance/2, x + w + self.clearance/2, y + l + self.clearance/2)
                    occupied_polygons.append(poly)
                    placed.append({
                        "name": item["name"],
                        "x": x,
                        "y": y,
                        "w": w,
                        "l": l,
                        "color": item["color"]
                    })
                    
            if rtype_mapped == "kitchen" and rw * rl > 12.0:
                ix, iy, iw, il = rx + rw/2 - 0.5, ry + rl/2 - 0.9, 1.0, 1.8
                ipoly = box(ix, iy, ix + iw, iy + il)
                can_place = True
                for op in occupied_polygons:
                    if ipoly.intersects(op):
                        can_place = False
                        break
                if can_place:
                    placed.append({
                        "name": "جزيرة مطبخ",
                        "x": ix, "y": iy, "w": iw, "l": il,
                        "color": "#D29922"
                    })
                    
            layouts[room["name"]] = placed
            
        return layouts

    def _map_room_type(self, rt: str) -> str:
        """تحويل نوع الغرفة"""
        if "bed" in rt or "نوم" in rt:
            return "bedroom"
        if "kitchen" in rt or "مطبخ" in rt:
            return "kitchen"
        if "bath" in rt or "حمام" in rt:
            return "bathroom"
        return "living"

    def _find_position(self, rx: float, ry: float, rw: float, rl: float, item: Dict[str, Any], occupied: List[Polygon]) -> Optional[Tuple[float, float, float, float]]:
        """إيجاد موقع مناسب لقطعة أثاث"""
        iw, il = item["w"], item["l"]
        
        candidates = []
        if item["req_wall"]:
            candidates.append((rx + self.clearance, ry + rl - il - self.clearance, iw, il))
            candidates.append((rx + rw - iw - self.clearance, ry + self.clearance, iw, il))
            candidates.append((rx + self.clearance, ry + self.clearance, il, iw))
        else:
            candidates.append((rx + rw/2 - iw/2, ry + rl/2 - il/2, iw, il))
            
        for cx, cy, cw, cl in candidates:
            if cx >= rx and cy >= ry and cx + cw <= rx + rw and cy + cl <= ry + rl:
                poly = box(cx - 0.1, cy - 0.1, cx + cw + 0.1, cy + cl + 0.1)
                conflict = False
                for op in occupied:
                    if poly.intersects(op):
                        conflict = True
                        break
                if not conflict:
                    return (cx, cy, cw, cl)
        return None

    def calculate_circulation_score(self, rx: float, ry: float, rw: float, rl: float, furniture: List[Dict[str, Any]]) -> float:
        """حساب مسارات الحركة"""
        total_area = rw * rl
        occupied_area = sum([f["w"] * f["l"] for f in furniture])
        clearance_area = occupied_area * 1.5
        score = 100.0 * (total_area - occupied_area - clearance_area) / total_area
        return max(0.0, min(100.0, score))
