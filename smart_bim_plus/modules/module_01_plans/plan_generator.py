import math
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import Polygon, MultiPolygon, box, LineString, Point
from shapely.affinity import translate, rotate
from shapely.ops import unary_union
import numpy as np


class FloorPlanGenerator:
    """مولد المخططات الطابقية — يستخدم خوارزمية التقسيم التعاودي"""

    ROOM_TEMPLATES = {
        "residential": {
            "living_room": {"min_area": 16, "max_area": 35, "ratio": (1.0, 1.6), "priority": 1},
            "kitchen": {"min_area": 8, "max_area": 18, "ratio": (0.8, 1.5), "priority": 2},
            "master_bedroom": {"min_area": 14, "max_area": 25, "ratio": (0.9, 1.4), "priority": 3},
            "bedroom": {"min_area": 10, "max_area": 18, "ratio": (0.9, 1.4), "priority": 4},
            "bathroom": {"min_area": 4, "max_area": 8, "ratio": (0.7, 1.3), "priority": 5},
            "guest_room": {"min_area": 12, "max_area": 20, "ratio": (1.0, 1.5), "priority": 6},
            "corridor": {"min_area": 4, "max_area": 12, "ratio": (0.3, 0.5), "priority": 7},
            "storage": {"min_area": 2, "max_area": 6, "ratio": (0.8, 1.2), "priority": 8},
        },
        "commercial": {
            "reception": {"min_area": 20, "max_area": 50, "ratio": (1.0, 2.0), "priority": 1},
            "office": {"min_area": 12, "max_area": 30, "ratio": (0.8, 1.5), "priority": 2},
            "meeting_room": {"min_area": 15, "max_area": 40, "ratio": (1.0, 1.5), "priority": 3},
            "server_room": {"min_area": 8, "max_area": 15, "ratio": (0.9, 1.2), "priority": 4},
            "kitchen": {"min_area": 8, "max_area": 12, "ratio": (0.8, 1.3), "priority": 5},
            "bathroom": {"min_area": 6, "max_area": 12, "ratio": (0.7, 1.3), "priority": 6},
            "corridor": {"min_area": 6, "max_area": 20, "ratio": (0.2, 0.4), "priority": 7},
            "storage": {"min_area": 4, "max_area": 10, "ratio": (0.8, 1.2), "priority": 8},
        },
        "tower": {
            "lobby": {"min_area": 30, "max_area": 80, "ratio": (1.0, 2.0), "priority": 1},
            "apartment": {"min_area": 60, "max_area": 150, "ratio": (0.8, 1.5), "priority": 2},
            "elevator_shaft": {"min_area": 6, "max_area": 10, "ratio": (0.9, 1.1), "priority": 3},
            "staircase": {"min_area": 8, "max_area": 15, "ratio": (0.5, 0.8), "priority": 4},
            "corridor": {"min_area": 10, "max_area": 30, "ratio": (0.2, 0.4), "priority": 5},
            "mechanical_room": {"min_area": 10, "max_area": 25, "ratio": (0.8, 1.2), "priority": 6},
        },
    }

    FLOOR_CONFIGS = {
        "residential": {
            1: [("living_room", 1), ("kitchen", 1), ("master_bedroom", 1),
                ("bathroom", 1), ("corridor", 1)],
            2: [("living_room", 1), ("kitchen", 1), ("master_bedroom", 1),
                ("bedroom", 1), ("bathroom", 2), ("guest_room", 1), ("corridor", 1)],
            3: [("living_room", 1), ("kitchen", 1), ("master_bedroom", 1),
                ("bedroom", 2), ("bathroom", 2), ("guest_room", 1),
                ("corridor", 1), ("storage", 1)],
        },
        "commercial": {
            1: [("reception", 1), ("office", 3), ("meeting_room", 1),
                ("bathroom", 2), ("corridor", 1)],
            2: [("reception", 1), ("office", 4), ("meeting_room", 2),
                ("server_room", 1), ("kitchen", 1), ("bathroom", 2), ("corridor", 1)],
        },
        "tower": {
            1: [("lobby", 1), ("elevator_shaft", 2), ("staircase", 1),
                ("corridor", 1), ("mechanical_room", 1)],
            "typical": [("apartment", 2), ("elevator_shaft", 2), ("staircase", 1),
                        ("corridor", 1)],
        },
    }

    def __init__(self):
        self.wall_thickness = 0.2
        self.door_width = 0.9
        self.window_width = 1.2
        self.min_room_dimension = 2.0

    def generate_floor_plan(self, building_type: str, plot_width: float,
                            plot_length: float, floor_number: int,
                            total_floors: int, style: str = "modern"
                            ) -> Dict[str, Any]:
        """توليد مخطط طابقي كامل"""
        templates = self.ROOM_TEMPLATES.get(building_type,
                                            self.ROOM_TEMPLATES["residential"])
        floor_config = self._get_floor_config(building_type, floor_number,
                                              total_floors)

        rooms_to_place = []
        for room_type, count in floor_config:
            tmpl = templates.get(room_type, {"min_area": 10, "max_area": 20,
                                             "ratio": (0.8, 1.5), "priority": 99})
            for i in range(count):
                target_area = (tmpl["min_area"] + tmpl["max_area"]) / 2
                ratio = (tmpl["ratio"][0] + tmpl["ratio"][1]) / 2
                w = math.sqrt(target_area / ratio)
                l = target_area / w
                rooms_to_place.append({
                    "room_type": room_type,
                    "name": self._room_name_ar(room_type, i + 1, count),
                    "target_area": target_area,
                    "width": round(w, 1),
                    "length": round(l, 1),
                    "area": round(w * l, 1),
                    "priority": tmpl["priority"],
                })

        setback = 0.3
        usable_width = plot_width - 2 * setback
        usable_length = plot_length - 2 * setback

        placed_rooms = self._place_rooms_recursive(
            rooms_to_place, setback, setback,
            usable_width, usable_length
        )

        walls = self._generate_walls(placed_rooms, plot_width, plot_length)
        doors = self._place_doors(placed_rooms)
        windows = self._place_windows(placed_rooms, plot_width, plot_length)

        return {
            "floor_number": floor_number,
            "building_type": building_type,
            "plot_width": plot_width,
            "plot_length": plot_length,
            "rooms": placed_rooms,
            "walls": walls,
            "doors": doors,
            "windows": windows,
            "total_area": sum(r["area"] for r in placed_rooms),
            "boundary": box(0, 0, plot_width, plot_length),
        }

    def _get_floor_config(self, building_type: str, floor_number: int,
                          total_floors: int):
        configs = self.FLOOR_CONFIGS.get(building_type,
                                         self.FLOOR_CONFIGS["residential"])
        if building_type == "tower":
            if floor_number == 0:
                return configs.get(1, configs.get("typical", []))
            return configs.get("typical", [])

        if floor_number in configs:
            return configs[floor_number]

        max_key = max(k for k in configs.keys() if isinstance(k, int))
        return configs[max_key]

    def _place_rooms_recursive(self, rooms: List[Dict],
                               x0: float, y0: float,
                               width: float, length: float
                               ) -> List[Dict]:
        """تقسيم تعاودي للمساحة لوضع الغرف"""
        if not rooms or width < self.min_room_dimension or length < self.min_room_dimension:
            return []

        rooms = sorted(rooms, key=lambda r: r["priority"])

        if len(rooms) == 1:
            room = dict(rooms[0])
            room["position_x"] = x0
            room["position_y"] = y0
            room["width"] = round(width, 2)
            room["length"] = round(length, 2)
            room["area"] = round(width * length, 2)
            room["polygon"] = box(x0, y0, x0 + width, y0 + length)
            room["has_window"] = True
            return [room]

        split_index = len(rooms) // 2
        group_a = rooms[:split_index]
        group_b = rooms[split_index:]

        area_a = sum(r["target_area"] for r in group_a)
        area_b = sum(r["target_area"] for r in group_b)
        total_area = area_a + area_b
        ratio_a = area_a / total_area if total_area > 0 else 0.5

        result = []
        wt = self.wall_thickness

        if width >= length:
            split_x = x0 + width * ratio_a - wt / 2
            left_w = width * ratio_a - wt / 2
            right_w = width * (1 - ratio_a) - wt / 2
            result.extend(self._place_rooms_recursive(
                group_a, x0, y0, max(left_w, self.min_room_dimension), length
            ))
            result.extend(self._place_rooms_recursive(
                group_b, split_x + wt, y0,
                max(right_w, self.min_room_dimension), length
            ))
        else:
            split_y = y0 + length * ratio_a - wt / 2
            top_l = length * ratio_a - wt / 2
            bot_l = length * (1 - ratio_a) - wt / 2
            result.extend(self._place_rooms_recursive(
                group_a, x0, y0, width, max(top_l, self.min_room_dimension)
            ))
            result.extend(self._place_rooms_recursive(
                group_b, x0, split_y + wt, width,
                max(bot_l, self.min_room_dimension)
            ))

        return result

    def _generate_walls(self, rooms: List[Dict],
                        plot_width: float, plot_length: float) -> List[Dict]:
        """توليد الجدران"""
        walls = []
        wt = self.wall_thickness

        outer_walls = [
            {"start": (0, 0), "end": (plot_width, 0), "type": "external"},
            {"start": (plot_width, 0), "end": (plot_width, plot_length), "type": "external"},
            {"start": (plot_width, plot_length), "end": (0, plot_length), "type": "external"},
            {"start": (0, plot_length), "end": (0, 0), "type": "external"},
        ]
        for w in outer_walls:
            w["thickness"] = wt * 1.5
        walls.extend(outer_walls)

        edges_seen = set()
        for room in rooms:
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 0)
            rl = room.get("length", 0)

            edges = [
                ((px, py), (px + rw, py)),
                ((px + rw, py), (px + rw, py + rl)),
                ((px + rw, py + rl), (px, py + rl)),
                ((px, py + rl), (px, py)),
            ]
            for s, e in edges:
                key = (round(s[0], 1), round(s[1], 1),
                       round(e[0], 1), round(e[1], 1))
                rev_key = (round(e[0], 1), round(e[1], 1),
                           round(s[0], 1), round(s[1], 1))
                if key not in edges_seen and rev_key not in edges_seen:
                    edges_seen.add(key)
                    walls.append({
                        "start": s, "end": e,
                        "type": "internal",
                        "thickness": wt,
                    })
        return walls

    def _place_doors(self, rooms: List[Dict]) -> List[Dict]:
        """وضع الأبواب"""
        doors = []
        for room in rooms:
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 0)

            door_x = px + rw * 0.3
            door_y = py

            doors.append({
                "position": (door_x, door_y),
                "width": self.door_width,
                "room_name": room.get("name", ""),
                "swing": "left" if room.get("room_type") != "bathroom" else "right",
            })
        return doors

    def _place_windows(self, rooms: List[Dict],
                       plot_width: float, plot_length: float) -> List[Dict]:
        """وضع النوافذ على الجدران الخارجية"""
        windows = []
        for room in rooms:
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 0)
            rl = room.get("length", 0)

            if room.get("room_type") in ("corridor", "storage", "elevator_shaft"):
                continue

            on_edge = False
            if abs(py) < 0.5 or abs(py + rl - plot_length) < 0.5:
                win_x = px + rw / 2 - self.window_width / 2
                win_y = py if abs(py) < 0.5 else py + rl
                windows.append({
                    "position": (win_x, win_y),
                    "width": self.window_width,
                    "height": 1.2,
                    "sill_height": 0.9,
                    "orientation": "south" if abs(py) < 0.5 else "north",
                })
                on_edge = True

            if abs(px) < 0.5 or abs(px + rw - plot_width) < 0.5:
                win_x = px if abs(px) < 0.5 else px + rw
                win_y = py + rl / 2 - self.window_width / 2
                windows.append({
                    "position": (win_x, win_y),
                    "width": self.window_width,
                    "height": 1.2,
                    "sill_height": 0.9,
                    "orientation": "west" if abs(px) < 0.5 else "east",
                })
                on_edge = True

            room["has_window"] = on_edge

        return windows

    def _room_name_ar(self, room_type: str, index: int, total: int) -> str:
        names = {
            "living_room": "صالة المعيشة",
            "kitchen": "المطبخ",
            "master_bedroom": "غرفة النوم الرئيسية",
            "bedroom": "غرفة نوم",
            "bathroom": "حمام",
            "guest_room": "غرفة الضيوف",
            "corridor": "ممر",
            "storage": "مخزن",
            "reception": "استقبال",
            "office": "مكتب",
            "meeting_room": "قاعة اجتماعات",
            "server_room": "غرفة الخوادم",
            "lobby": "بهو",
            "apartment": "شقة",
            "elevator_shaft": "بئر المصعد",
            "staircase": "درج",
            "mechanical_room": "غرفة ميكانيكية",
        }
        base = names.get(room_type, room_type)
        if total > 1:
            return f"{base} {index}"
        return base

    def get_room_polygons(self, plan_data: Dict) -> List[Tuple[Polygon, Dict]]:
        result = []
        for room in plan_data.get("rooms", []):
            poly = room.get("polygon")
            if poly is None:
                px = room.get("position_x", 0)
                py = room.get("position_y", 0)
                rw = room.get("width", 0)
                rl = room.get("length", 0)
                poly = box(px, py, px + rw, py + rl)
            result.append((poly, room))
        return result
