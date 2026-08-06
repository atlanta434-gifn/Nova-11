import ezdxf
from ezdxf.enums import TextEntityAlignment
from typing import Dict, Any, List


class DXFExporter:
    """مصدر ملفات DXF — ينشئ رسومات CAD لكل طابق"""

    LAYER_CONFIG = {
        "WALLS_EXT": {"color": 7, "lineweight": 50},
        "WALLS_INT": {"color": 8, "lineweight": 30},
        "DOORS": {"color": 3, "lineweight": 18},
        "WINDOWS": {"color": 5, "lineweight": 18},
        "DIMENSIONS": {"color": 1, "lineweight": 13},
        "ROOM_NAMES": {"color": 2, "lineweight": 13},
        "FURNITURE": {"color": 4, "lineweight": 13},
        "GRID": {"color": 9, "lineweight": 13},
        "BOUNDARY": {"color": 6, "lineweight": 35},
        "HATCHING": {"color": 251, "lineweight": 13},
    }

    def __init__(self):
        self.doc = None
        self.msp = None
        self.scale = 1.0

    def export(self, plan_data: Dict[str, Any], filepath: str,
               scale: float = 100.0):
        """تصدير المخطط إلى ملف DXF"""
        self.scale = scale
        self.doc = ezdxf.new("R2013", setup=True)
        self.msp = self.doc.modelspace()

        self._setup_layers()
        self._draw_boundary(plan_data)
        self._draw_rooms(plan_data)
        self._draw_walls(plan_data)
        self._draw_doors(plan_data)
        self._draw_windows(plan_data)
        self._draw_dimensions(plan_data)
        self._draw_room_labels(plan_data)
        self._draw_title_block(plan_data)

        self.doc.saveas(filepath)

    def _setup_layers(self):
        for name, cfg in self.LAYER_CONFIG.items():
            self.doc.layers.add(
                name,
                color=cfg["color"],
                dxfattribs={"lineweight": cfg["lineweight"]},
            )

    def _s(self, val: float) -> float:
        return val * self.scale

    def _draw_boundary(self, plan_data: Dict):
        w = self._s(plan_data.get("plot_width", 20))
        l = self._s(plan_data.get("plot_length", 25))
        self.msp.add_lwpolyline(
            [(0, 0), (w, 0), (w, l), (0, l), (0, 0)],
            dxfattribs={"layer": "BOUNDARY"},
        )

    def _draw_rooms(self, plan_data: Dict):
        for room in plan_data.get("rooms", []):
            px = self._s(room.get("position_x", 0))
            py = self._s(room.get("position_y", 0))
            rw = self._s(room.get("width", 0))
            rl = self._s(room.get("length", 0))
            self.msp.add_lwpolyline(
                [(px, py), (px + rw, py), (px + rw, py + rl),
                 (px, py + rl), (px, py)],
                dxfattribs={"layer": "WALLS_INT"},
            )

    def _draw_walls(self, plan_data: Dict):
        for wall in plan_data.get("walls", []):
            sx, sy = wall["start"]
            ex, ey = wall["end"]
            layer = "WALLS_EXT" if wall.get("type") == "external" else "WALLS_INT"
            self.msp.add_line(
                (self._s(sx), self._s(sy)),
                (self._s(ex), self._s(ey)),
                dxfattribs={"layer": layer},
            )

    def _draw_doors(self, plan_data: Dict):
        for door in plan_data.get("doors", []):
            pos = door["position"]
            px, py = self._s(pos[0]), self._s(pos[1])
            dw = self._s(door.get("width", 0.9))

            self.msp.add_line(
                (px, py - 2), (px, py + 2),
                dxfattribs={"layer": "DOORS"},
            )
            self.msp.add_line(
                (px + dw, py - 2), (px + dw, py + 2),
                dxfattribs={"layer": "DOORS"},
            )

            import math
            arc_radius = dw
            self.msp.add_arc(
                center=(px, py),
                radius=arc_radius,
                start_angle=0,
                end_angle=90,
                dxfattribs={"layer": "DOORS"},
            )

    def _draw_windows(self, plan_data: Dict):
        for win in plan_data.get("windows", []):
            pos = win["position"]
            px, py = self._s(pos[0]), self._s(pos[1])
            ww = self._s(win.get("width", 1.2))
            orient = win.get("orientation", "south")

            if orient in ("south", "north"):
                self.msp.add_line(
                    (px, py - 3), (px, py + 3),
                    dxfattribs={"layer": "WINDOWS"},
                )
                self.msp.add_line(
                    (px + ww, py - 3), (px + ww, py + 3),
                    dxfattribs={"layer": "WINDOWS"},
                )
                self.msp.add_line(
                    (px, py), (px + ww, py),
                    dxfattribs={"layer": "WINDOWS"},
                )
            else:
                self.msp.add_line(
                    (px - 3, py), (px + 3, py),
                    dxfattribs={"layer": "WINDOWS"},
                )
                self.msp.add_line(
                    (px - 3, py + ww), (px + 3, py + ww),
                    dxfattribs={"layer": "WINDOWS"},
                )
                self.msp.add_line(
                    (px, py), (px, py + ww),
                    dxfattribs={"layer": "WINDOWS"},
                )

    def _draw_dimensions(self, plan_data: Dict):
        pw = plan_data.get("plot_width", 20)
        pl = plan_data.get("plot_length", 25)

        offset = self._s(1.5)
        self.msp.add_aligned_dim(
            p1=(0, -offset),
            p2=(self._s(pw), -offset),
            distance=self._s(0.5),
            dxfattribs={"layer": "DIMENSIONS"},
        ).render()

        self.msp.add_aligned_dim(
            p1=(-offset, 0),
            p2=(-offset, self._s(pl)),
            distance=self._s(0.5),
            dxfattribs={"layer": "DIMENSIONS"},
        ).render()

        for room in plan_data.get("rooms", []):
            px = self._s(room.get("position_x", 0))
            py = self._s(room.get("position_y", 0))
            rw = self._s(room.get("width", 0))
            rl = self._s(room.get("length", 0))

            self.msp.add_aligned_dim(
                p1=(px, py - self._s(0.3)),
                p2=(px + rw, py - self._s(0.3)),
                distance=self._s(0.2),
                override={"dimtxt": self._s(0.15)},
                dxfattribs={"layer": "DIMENSIONS"},
            ).render()

    def _draw_room_labels(self, plan_data: Dict):
        for room in plan_data.get("rooms", []):
            px = self._s(room.get("position_x", 0))
            py = self._s(room.get("position_y", 0))
            rw = self._s(room.get("width", 0))
            rl = self._s(room.get("length", 0))

            cx = px + rw / 2
            cy = py + rl / 2

            name = room.get("name", room.get("room_type", ""))
            self.msp.add_text(
                name,
                height=self._s(0.2),
                dxfattribs={
                    "layer": "ROOM_NAMES",
                    "style": "Standard",
                },
            ).set_placement(
                (cx, cy),
                align=TextEntityAlignment.MIDDLE_CENTER,
            )

            area_text = f"{room.get('area', 0):.1f} م²"
            self.msp.add_text(
                area_text,
                height=self._s(0.15),
                dxfattribs={
                    "layer": "ROOM_NAMES",
                    "style": "Standard",
                },
            ).set_placement(
                (cx, cy - self._s(0.4)),
                align=TextEntityAlignment.MIDDLE_CENTER,
            )

    def _draw_title_block(self, plan_data: Dict):
        pw = self._s(plan_data.get("plot_width", 20))
        pl = self._s(plan_data.get("plot_length", 25))

        tb_x = pw + self._s(2)
        tb_y = 0
        tb_w = self._s(8)
        tb_h = self._s(5)

        self.msp.add_lwpolyline(
            [(tb_x, tb_y), (tb_x + tb_w, tb_y),
             (tb_x + tb_w, tb_y + tb_h), (tb_x, tb_y + tb_h),
             (tb_x, tb_y)],
            dxfattribs={"layer": "BOUNDARY"},
        )

        self.msp.add_text(
            "NOVA",
            height=self._s(0.3),
            dxfattribs={"layer": "ROOM_NAMES"},
        ).set_placement(
            (tb_x + tb_w / 2, tb_y + tb_h - self._s(0.5)),
            align=TextEntityAlignment.MIDDLE_CENTER,
        )

        bt = plan_data.get("building_type", "residential")
        fn = plan_data.get("floor_number", 0)
        self.msp.add_text(
            f"Floor {fn} - {bt}",
            height=self._s(0.2),
            dxfattribs={"layer": "ROOM_NAMES"},
        ).set_placement(
            (tb_x + tb_w / 2, tb_y + tb_h - self._s(1.2)),
            align=TextEntityAlignment.MIDDLE_CENTER,
        )

        ta = sum(r.get("area", 0) for r in plan_data.get("rooms", []))
        self.msp.add_text(
            f"Total Area: {ta:.1f} m2",
            height=self._s(0.15),
            dxfattribs={"layer": "DIMENSIONS"},
        ).set_placement(
            (tb_x + tb_w / 2, tb_y + tb_h - self._s(1.8)),
            align=TextEntityAlignment.MIDDLE_CENTER,
        )

        self.msp.add_text(
            f"Scale: 1:{int(self.scale)}",
            height=self._s(0.15),
            dxfattribs={"layer": "DIMENSIONS"},
        ).set_placement(
            (tb_x + tb_w / 2, tb_y + tb_h - self._s(2.3)),
            align=TextEntityAlignment.MIDDLE_CENTER,
        )
