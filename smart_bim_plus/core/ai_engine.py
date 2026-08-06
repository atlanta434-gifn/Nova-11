import os
import logging
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger("SmartBIM.AIEngine")


class AIEngine:
    """محرك الذكاء الاصطناعي — DSBA Algorithm Core
    يدير نماذج ONNX المحلية مع خيار احتياطي قائم على القواعد"""

    SUPPORTED_PROVIDERS = [
        "DmlExecutionProvider",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    ]

    def __init__(self, models_dir: str = "ai_models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Any] = {}
        self.available_providers: List[str] = []
        self.is_onnx_available = False
        
        # Initialize RAG Engine
        from core.rag_engine import RAGEngine
        self.rag = RAGEngine()
        self.rag.initialize_rag()
        
        self._initialize_runtime()

    def _initialize_runtime(self):
        """تهيئة محرك ONNX Runtime"""
        try:
            import onnxruntime as ort
            self.is_onnx_available = True
            all_providers = ort.get_available_providers()
            self.available_providers = [
                p for p in self.SUPPORTED_PROVIDERS if p in all_providers
            ]
            if not self.available_providers:
                self.available_providers = ["CPUExecutionProvider"]
            logger.info(f"ONNX Runtime initialized: {self.available_providers}")
        except ImportError:
            self.is_onnx_available = False
            logger.warning("ONNX Runtime not found, using rule-based fallback")

    def get_status(self) -> Dict[str, Any]:
        """الحصول على حالة المحرك"""
        discovered = self._discover_models()
        return {
            "onnx_available": self.is_onnx_available,
            "providers": self.available_providers,
            "models_found": len(discovered),
            "models_loaded": len(self.sessions),
            "model_names": list(discovered.keys()),
            "mode": "onnx" if self.is_onnx_available and discovered else "rule_based",
        }

    def _discover_models(self) -> Dict[str, Path]:
        found = {}
        if self.models_dir.exists():
            for f in self.models_dir.glob("*.onnx"):
                found[f.stem] = f
        return found

    def load_model(self, model_name: str) -> bool:
        """تحميل نموذج ONNX"""
        if not self.is_onnx_available:
            logger.warning(f"Cannot load {model_name}: ONNX not available")
            return False
        models = self._discover_models()
        if model_name not in models:
            logger.warning(f"Model {model_name} not found in {self.models_dir}")
            return False
        try:
            import onnxruntime as ort
            opts = ort.SessionOptions()
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            opts.intra_op_num_threads = os.cpu_count() or 4
            session = ort.InferenceSession(
                str(models[model_name]),
                sess_options=opts,
                providers=self.available_providers,
            )
            self.sessions[model_name] = session
            logger.info(f"Model {model_name} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False

    def predict(self, model_name: str, input_data: np.ndarray) -> Optional[np.ndarray]:
        """تنفيذ تنبؤ باستخدام نموذج محمل"""
        if model_name not in self.sessions:
            if not self.load_model(model_name):
                return None
        try:
            session = self.sessions[model_name]
            input_name = session.get_inputs()[0].name
            result = session.run(None, {input_name: input_data.astype(np.float32)})
            return result[0]
        except Exception as e:
            logger.error(f"Prediction failed for {model_name}: {e}")
            return None

    def query_rag(self, question: str) -> str:
        """استعلام من محرك RAG"""
        return self.rag.query(question)

    def optimize_layout(self, rooms: List[Dict], constraints: Dict) -> List[Dict]:
        """تحسين تخطيط الغرف — DSBA Stage 4
        يحاول استخدام نموذج ONNX أولاً، ثم يرجع للقواعد"""
        if "layout_optimizer" in self.sessions:
            try:
                features = self._rooms_to_features(rooms, constraints)
                result = self.predict("layout_optimizer", features)
                if result is not None:
                    return self._features_to_rooms(result, rooms)
            except Exception as e:
                logger.warning(f"ONNX layout optimization failed: {e}")

        return self._rule_based_layout(rooms, constraints)

    def _rule_based_layout(self, rooms: List[Dict],
                           constraints: Dict) -> List[Dict]:
        """محسن تخطيط قائم على القواعد"""
        plot_width = constraints.get("plot_width", 20.0)
        plot_length = constraints.get("plot_length", 25.0)
        building_type = constraints.get("building_type", "residential")
        orientation = constraints.get("orientation", 0.0)

        priority_order = {
            "residential": [
                "living_room", "kitchen", "master_bedroom", "bedroom",
                "bathroom", "guest_room", "storage", "corridor",
            ],
            "commercial": [
                "reception", "office", "meeting_room", "server_room",
                "kitchen", "bathroom", "storage", "corridor",
            ],
            "tower": [
                "lobby", "elevator_shaft", "staircase", "apartment",
                "corridor", "mechanical_room", "storage",
            ],
        }

        order = priority_order.get(building_type, priority_order["residential"])
        sorted_rooms = sorted(
            rooms,
            key=lambda r: order.index(r.get("room_type", "storage"))
            if r.get("room_type", "storage") in order else 99,
        )

        margin = 0.2
        usable_width = plot_width - 2 * margin
        usable_length = plot_length - 2 * margin

        placed = []
        cursor_x = margin
        cursor_y = margin
        row_height = 0.0

        for room in sorted_rooms:
            w = room.get("width", 4.0)
            l = room.get("length", 4.0)

            if cursor_x + w > usable_width + margin:
                cursor_x = margin
                cursor_y += row_height + margin
                row_height = 0.0

            if cursor_y + l > usable_length + margin:
                break

            placed_room = dict(room)
            placed_room["position_x"] = cursor_x
            placed_room["position_y"] = cursor_y
            placed.append(placed_room)

            cursor_x += w + margin
            row_height = max(row_height, l)

        return placed

    def score_design(self, building_data: Dict,
                     standard: str = "IQS") -> Dict[str, Any]:
        """تقييم التصميم وفق معايير البناء العراقية"""
        scores = {}

        rooms = building_data.get("rooms", [])
        total_area = building_data.get("total_area", 0)
        plot_area = building_data.get("plot_width", 1) * building_data.get("plot_length", 1)
        building_ratio = total_area / plot_area if plot_area > 0 else 0

        if building_ratio <= 0.6:
            scores["coverage_ratio"] = 100
        elif building_ratio <= 0.7:
            scores["coverage_ratio"] = 80
        elif building_ratio <= 0.8:
            scores["coverage_ratio"] = 60
        else:
            scores["coverage_ratio"] = 30

        window_rooms = sum(1 for r in rooms if r.get("has_window", False))
        if rooms:
            ventilation_ratio = window_rooms / len(rooms)
            scores["natural_ventilation"] = min(100, int(ventilation_ratio * 120))
        else:
            scores["natural_ventilation"] = 0

        min_areas = {
            "living_room": 16, "bedroom": 10, "master_bedroom": 14,
            "kitchen": 8, "bathroom": 4, "guest_room": 12,
        }
        area_scores = []
        for room in rooms:
            rt = room.get("room_type", "")
            area = room.get("area", 0)
            min_a = min_areas.get(rt, 6)
            area_scores.append(min(100, int((area / min_a) * 100)) if min_a > 0 else 100)
        scores["room_sizes"] = int(np.mean(area_scores)) if area_scores else 0

        scores["structural_safety"] = 85
        scores["fire_safety"] = 75
        scores["energy_efficiency"] = 70

        overall = int(np.mean(list(scores.values())))
        return {
            "overall": overall,
            "details": scores,
            "standard": standard,
            "grade": "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D",
            "recommendations": self._generate_recommendations(scores),
        }

    def _generate_recommendations(self, scores: Dict[str, int]) -> List[str]:
        recs = []
        if scores.get("coverage_ratio", 100) < 70:
            recs.append("تقليل نسبة البناء للأرض لتحسين التهوية والإضاءة الطبيعية")
        if scores.get("natural_ventilation", 100) < 80:
            recs.append("إضافة نوافذ أو فتحات تهوية للغرف المغلقة")
        if scores.get("room_sizes", 100) < 70:
            recs.append("مراجعة أحجام الغرف وفق الحد الأدنى المطلوب بالمعايير")
        if scores.get("energy_efficiency", 100) < 75:
            recs.append("إضافة عزل حراري وألواح شمسية لتحسين كفاءة الطاقة")
        if scores.get("fire_safety", 100) < 80:
            recs.append("مراجعة مخارج الطوارئ وأنظمة الإطفاء")
        return recs

    def generate_alternatives(self, building_data: Dict,
                              count: int = 3) -> List[Dict]:
        """توليد بدائل تصميمية مصنفة"""
        alternatives = []
        rooms = building_data.get("rooms", [])
        constraints = {
            "plot_width": building_data.get("plot_width", 20),
            "plot_length": building_data.get("plot_length", 25),
            "building_type": building_data.get("building_type", "residential"),
        }

        for i in range(count):
            modified_rooms = []
            for room in rooms:
                mr = dict(room)
                scale = 1.0 + (i - 1) * 0.15
                mr["width"] = room.get("width", 4.0) * scale
                mr["length"] = room.get("length", 4.0) * scale
                mr["area"] = mr["width"] * mr["length"]
                modified_rooms.append(mr)

            layout = self.optimize_layout(modified_rooms, constraints)
            alt_data = dict(building_data)
            alt_data["rooms"] = layout
            alt_data["total_area"] = sum(r.get("area", 0) for r in layout)
            score = self.score_design(alt_data)

            labels = ["اقتصادي", "متوازن", "فاخر"]
            alternatives.append({
                "name": labels[i] if i < len(labels) else f"بديل {i + 1}",
                "rooms": layout,
                "score": score,
                "total_area": alt_data["total_area"],
                "estimated_cost": self._estimate_cost(alt_data),
            })

        alternatives.sort(key=lambda x: x["score"]["overall"], reverse=True)
        return alternatives

    def _estimate_cost(self, building_data: Dict) -> float:
        area = building_data.get("total_area", 0)
        floors = building_data.get("total_floors", 1)
        bt = building_data.get("building_type", "residential")
        cost_per_m2 = {
            "residential": 450,
            "commercial": 600,
            "tower": 700,
            "mall": 550,
            "industrial": 350,
        }
        base = cost_per_m2.get(bt, 500)
        return area * floors * base

    def _rooms_to_features(self, rooms: List[Dict],
                           constraints: Dict) -> np.ndarray:
        features = []
        for room in rooms:
            features.extend([
                room.get("width", 0), room.get("length", 0),
                room.get("area", 0), room.get("position_x", 0),
                room.get("position_y", 0),
            ])
        while len(features) < 100:
            features.append(0.0)
        return np.array([features[:100]], dtype=np.float32)

    def _features_to_rooms(self, result: np.ndarray,
                           original_rooms: List[Dict]) -> List[Dict]:
        optimized = []
        flat = result.flatten()
        for i, room in enumerate(original_rooms):
            r = dict(room)
            idx = i * 5
            if idx + 4 < len(flat):
                r["position_x"] = float(flat[idx + 3])
                r["position_y"] = float(flat[idx + 4])
            optimized.append(r)
        return optimized

    def process_point_cloud(self, points: np.ndarray) -> Dict[str, Any]:
        """معالجة سحابة النقاط — DSBA Stage 2
        تجزئة ذكية باستخدام DBSCAN"""
        try:
            from sklearn.cluster import DBSCAN

            z_values = points[:, 2]
            ground_threshold = np.percentile(z_values, 10)
            roof_threshold = np.percentile(z_values, 90)

            ground_mask = z_values <= ground_threshold + 0.3
            roof_mask = z_values >= roof_threshold - 0.3
            wall_mask = ~ground_mask & ~roof_mask

            wall_points = points[wall_mask]
            clustering = DBSCAN(eps=0.5, min_samples=10).fit(wall_points[:, :2])
            wall_labels = clustering.labels_
            n_walls = len(set(wall_labels)) - (1 if -1 in wall_labels else 0)

            ground_area = self._calculate_area_2d(points[ground_mask][:, :2])
            building_height = float(np.percentile(z_values, 95) - np.percentile(z_values, 5))
            perimeter = self._calculate_perimeter(points[ground_mask][:, :2])

            return {
                "ground_area": ground_area,
                "building_height": building_height,
                "perimeter": perimeter,
                "wall_count": n_walls,
                "ground_points": int(ground_mask.sum()),
                "wall_points": int(wall_mask.sum()),
                "roof_points": int(roof_mask.sum()),
                "total_points": len(points),
            }
        except Exception as e:
            logger.error(f"Point cloud processing failed: {e}")
            return {}

    def _calculate_area_2d(self, points_2d: np.ndarray) -> float:
        if len(points_2d) < 3:
            return 0.0
        try:
            from shapely.geometry import MultiPoint
            hull = MultiPoint(points_2d).convex_hull
            return float(hull.area)
        except Exception:
            x_range = points_2d[:, 0].max() - points_2d[:, 0].min()
            y_range = points_2d[:, 1].max() - points_2d[:, 1].min()
            return float(x_range * y_range)

    def _calculate_perimeter(self, points_2d: np.ndarray) -> float:
        if len(points_2d) < 3:
            return 0.0
        try:
            from shapely.geometry import MultiPoint
            hull = MultiPoint(points_2d).convex_hull
            return float(hull.length)
        except Exception:
            return 0.0

    def unload_model(self, model_name: str):
        if model_name in self.sessions:
            del self.sessions[model_name]
            logger.info(f"Model {model_name} unloaded")

    def unload_all(self):
        self.sessions.clear()
        logger.info("All models unloaded")
