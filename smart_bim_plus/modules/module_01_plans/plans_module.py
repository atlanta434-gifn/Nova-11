import numpy as np
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QCheckBox,
)
from PyQt6.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.patches import Rectangle, FancyArrowPatch, Arc
import matplotlib.pyplot as plt

from modules.base_module import BaseModule
from modules.module_01_plans.plan_generator import FloorPlanGenerator
from modules.module_01_plans.dxf_exporter import DXFExporter
from modules.module_01_plans.ifc_exporter import IFCExporter


class PlansModule(BaseModule):
    """وحدة المخططات المعمارية — النظام الأول
    توليد مخططات طابقية تلقائية مع تصدير DXF و IFC"""

    SYSTEM_NUMBER = 1
    SYSTEM_NAME = "Building Plans"
    SYSTEM_NAME_AR = "المخططات المعمارية"
    ICON_NAME = "plans"

    ROOM_COLORS = {
        "living_room": "#4A90D9",
        "kitchen": "#E8A838",
        "master_bedroom": "#7B68EE",
        "bedroom": "#9B8FE0",
        "bathroom": "#50C878",
        "guest_room": "#FF7F7F",
        "corridor": "#C0C0C0",
        "storage": "#A0A0A0",
        "reception": "#FFD700",
        "office": "#87CEEB",
        "meeting_room": "#DDA0DD",
        "server_room": "#708090",
        "lobby": "#F0E68C",
        "apartment": "#ADD8E6",
        "elevator_shaft": "#696969",
        "staircase": "#B0B0B0",
        "mechanical_room": "#808080",
    }

    def __init__(self, parent: Optional[QWidget] = None):
        self.generator = FloorPlanGenerator()
        self.dxf_exporter = DXFExporter()
        self.ifc_exporter = IFCExporter()
        self.current_plan = None
        self.figure = None
        self.canvas = None
        super().__init__(parent)

    def setup_input_panel(self):
        """إعداد لوحة إدخال بيانات المبنى"""
        type_group = QGroupBox("نوع المبنى")
        type_layout = QFormLayout(type_group)

        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems([
            "سكني - Residential",
            "تجاري - Commercial",
            "برج - Tower",
        ])
        type_layout.addRow("النوع:", self.building_type_combo)

        self.style_combo = QComboBox()
        self.style_combo.addItems(["حديث", "كلاسيكي", "عربي", "معاصر"])
        type_layout.addRow("الطراز:", self.style_combo)

        self.input_layout.addWidget(type_group)

        dim_group = QGroupBox("الأبعاد (متر)")
        dim_layout = QFormLayout(dim_group)

        self.plot_width_spin = QDoubleSpinBox()
        self.plot_width_spin.setRange(5.0, 10000.0)
        self.plot_width_spin.setValue(15.0)
        self.plot_width_spin.setSuffix(" م")
        self.plot_width_spin.setSingleStep(0.5)
        dim_layout.addRow("الواجهة:", self.plot_width_spin)

        self.plot_length_spin = QDoubleSpinBox()
        self.plot_length_spin.setRange(5.0, 10000.0)
        self.plot_length_spin.setValue(20.0)
        self.plot_length_spin.setSuffix(" م")
        self.plot_length_spin.setSingleStep(0.5)
        dim_layout.addRow("النزال:", self.plot_length_spin)

        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(25.0, 1000000.0)
        self.area_spin.setValue(300.0)
        self.area_spin.setSuffix(" م²")
        self.area_spin.setSingleStep(10.0)
        dim_layout.addRow("المساحة الكلية:", self.area_spin)

        self.plot_width_spin.valueChanged.connect(self._update_area)
        self.plot_length_spin.valueChanged.connect(self._update_area)
        self.area_spin.valueChanged.connect(self._update_length_from_area)

        self.floor_height_spin = QDoubleSpinBox()
        self.floor_height_spin.setRange(2.5, 6.0)
        self.floor_height_spin.setValue(3.0)
        self.floor_height_spin.setSuffix(" م")
        self.floor_height_spin.setSingleStep(0.1)
        dim_layout.addRow("ارتفاع الطابق:", self.floor_height_spin)

        self.input_layout.addWidget(dim_group)

        floor_group = QGroupBox("الطوابق")
        floor_layout = QFormLayout(floor_group)

        self.total_floors_spin = QSpinBox()
        self.total_floors_spin.setRange(1, 100)
        self.total_floors_spin.setValue(2)
        floor_layout.addRow("عدد الطوابق:", self.total_floors_spin)

        self.basement_spin = QSpinBox()
        self.basement_spin.setRange(0, 5)
        self.basement_spin.setValue(0)
        floor_layout.addRow("طوابق القبو:", self.basement_spin)

        self.current_floor_spin = QSpinBox()
        self.current_floor_spin.setRange(0, 100)
        self.current_floor_spin.setValue(0)
        floor_layout.addRow("الطابق الحالي:", self.current_floor_spin)

        self.input_layout.addWidget(floor_group)

        options_group = QGroupBox("خيارات إضافية")
        options_layout = QVBoxLayout(options_group)

        self.show_dimensions_cb = QCheckBox("إظهار الأبعاد")
        self.show_dimensions_cb.setChecked(True)
        self.show_dimensions_cb.stateChanged.connect(self._refresh_canvas)
        options_layout.addWidget(self.show_dimensions_cb)

        self.show_furniture_cb = QCheckBox("إظهار الأثاث")
        self.show_furniture_cb.setChecked(False)
        options_layout.addWidget(self.show_furniture_cb)

        self.show_grid_cb = QCheckBox("إظهار الشبكة")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.stateChanged.connect(self._refresh_canvas)
        options_layout.addWidget(self.show_grid_cb)

        self.input_layout.addWidget(options_group)

    def setup_canvas(self):
        """إعداد لوحة الرسم Matplotlib"""
        self.figure = Figure(figsize=(10, 8), facecolor="#0D1117")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        self._draw_empty_canvas()

    def _update_area(self, _=None):
        if not self.area_spin.hasFocus():
            w = self.plot_width_spin.value()
            l = self.plot_length_spin.value()
            self.area_spin.blockSignals(True)
            self.area_spin.setValue(w * l)
            self.area_spin.blockSignals(False)

    def _update_length_from_area(self, value):
        if self.area_spin.hasFocus():
            w = self.plot_width_spin.value()
            if w > 0:
                self.plot_length_spin.blockSignals(True)
                self.plot_length_spin.setValue(value / w)
                self.plot_length_spin.blockSignals(False)

    def _draw_empty_canvas(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#161B22")
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 25)
        ax.set_aspect("equal")
        ax.text(10, 12.5, "اضغط 'توليد' لإنشاء المخطط",
                ha="center", va="center", fontsize=14,
                color="#8B949E", fontfamily="sans-serif")
        ax.tick_params(colors="#30363D")
        for spine in ax.spines.values():
            spine.set_color("#30363D")
        self.canvas.draw()

    def generate(self):
        """توليد المخطط الطابقي"""
        bt_map = {
            "سكني - Residential": "residential",
            "تجاري - Commercial": "commercial",
            "برج - Tower": "tower",
        }
        building_type = bt_map.get(
            self.building_type_combo.currentText(), "residential"
        )
        plot_width = self.plot_width_spin.value()
        plot_length = self.plot_length_spin.value()
        floor_number = self.current_floor_spin.value()
        total_floors = self.total_floors_spin.value()

        self.current_plan = self.generator.generate_floor_plan(
            building_type=building_type,
            plot_width=plot_width,
            plot_length=plot_length,
            floor_number=floor_number,
            total_floors=total_floors,
            style=self.style_combo.currentText(),
        )
        self.generated_data = self.current_plan

        self._draw_plan()
        self.progress_updated.emit(100)

    def _draw_plan(self):
        if not self.current_plan:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#161B22")

        pw = self.current_plan["plot_width"]
        pl = self.current_plan["plot_length"]

        boundary = Rectangle(
            (0, 0), pw, pl,
            linewidth=2.5, edgecolor="#58A6FF",
            facecolor="none", linestyle="--",
        )
        ax.add_patch(boundary)

        for room in self.current_plan.get("rooms", []):
            px = room.get("position_x", 0)
            py = room.get("position_y", 0)
            rw = room.get("width", 0)
            rl = room.get("length", 0)
            rt = room.get("room_type", "storage")
            color = self.ROOM_COLORS.get(rt, "#808080")

            rect = Rectangle(
                (px, py), rw, rl,
                linewidth=1.5, edgecolor="#C9D1D9",
                facecolor=color, alpha=0.35,
            )
            ax.add_patch(rect)

            cx, cy = px + rw / 2, py + rl / 2
            name = room.get("name", rt)
            fontsize = min(9, max(6, int(min(rw, rl) * 1.8)))
            ax.text(cx, cy + 0.2, name,
                    ha="center", va="center",
                    fontsize=fontsize, color="#FFFFFF",
                    fontweight="bold", fontfamily="sans-serif")
            ax.text(cx, cy - 0.4, f"{room.get('area', 0):.1f} م²",
                    ha="center", va="center",
                    fontsize=fontsize - 1, color="#8B949E",
                    fontfamily="sans-serif")

        for door in self.current_plan.get("doors", []):
            pos = door["position"]
            dw = door.get("width", 0.9)
            arc = Arc(pos, dw * 2, dw * 2, angle=0,
                      theta1=0, theta2=90,
                      linewidth=1.5, color="#3FB950")
            ax.add_patch(arc)
            ax.plot([pos[0], pos[0]], [pos[1] - 0.1, pos[1] + 0.1],
                    color="#3FB950", linewidth=2)

        for win in self.current_plan.get("windows", []):
            pos = win["position"]
            ww = win.get("width", 1.2)
            orient = win.get("orientation", "south")
            if orient in ("south", "north"):
                ax.plot([pos[0], pos[0] + ww], [pos[1], pos[1]],
                        color="#58A6FF", linewidth=3)
                ax.plot([pos[0], pos[0] + ww],
                        [pos[1] - 0.05, pos[1] - 0.05],
                        color="#58A6FF", linewidth=1)
                ax.plot([pos[0], pos[0] + ww],
                        [pos[1] + 0.05, pos[1] + 0.05],
                        color="#58A6FF", linewidth=1)
            else:
                ax.plot([pos[0], pos[0]], [pos[1], pos[1] + ww],
                        color="#58A6FF", linewidth=3)

        if self.show_dimensions_cb.isChecked():
            self._draw_dimensions(ax, pw, pl)

        if self.show_grid_cb.isChecked():
            ax.set_xticks(np.arange(0, pw + 1, 1), minor=True)
            ax.set_yticks(np.arange(0, pl + 1, 1), minor=True)
            ax.grid(True, which="minor", color="#21262D",
                    linewidth=0.5, alpha=0.5)

        margin = 3
        ax.set_xlim(-margin, pw + margin)
        ax.set_ylim(-margin, pl + margin)
        ax.set_aspect("equal")
        ax.tick_params(colors="#484F58", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#30363D")

        fn = self.current_plan.get("floor_number", 0)
        bt = self.current_plan.get("building_type", "")
        ta = sum(r.get("area", 0) for r in self.current_plan.get("rooms", []))
        title = f"الطابق {fn} — {bt} — المساحة: {ta:.1f} م²"
        ax.set_title(title, color="#C9D1D9", fontsize=12,
                     fontfamily="sans-serif", pad=15)

        self.figure.tight_layout()
        self.canvas.draw()

    def _draw_dimensions(self, ax, pw: float, pl: float):
        offset = 1.2

        ax.annotate("", xy=(pw, -offset), xytext=(0, -offset),
                     arrowprops=dict(arrowstyle="<->", color="#F85149", lw=1.2))
        ax.text(pw / 2, -offset - 0.4, f"{pw:.1f} م",
                ha="center", va="center", fontsize=8, color="#F85149")

        ax.annotate("", xy=(-offset, pl), xytext=(-offset, 0),
                     arrowprops=dict(arrowstyle="<->", color="#F85149", lw=1.2))
        ax.text(-offset - 0.5, pl / 2, f"{pl:.1f} م",
                ha="center", va="center", fontsize=8, color="#F85149",
                rotation=90)

    def _refresh_canvas(self):
        if self.current_plan:
            self._draw_plan()

    def export_dxf(self, filepath: str):
        """تصدير المخطط إلى ملف DXF"""
        if not self.current_plan:
            raise ValueError("لا يوجد مخطط لتصديره")
        self.dxf_exporter.export(self.current_plan, filepath)

    def export_ifc(self, filepath: str):
        """تصدير المخطط إلى ملف IFC"""
        if not self.current_plan:
            raise ValueError("لا يوجد مخطط لتصديره")
        self.ifc_exporter.export(
            self.current_plan, filepath,
            total_floors=self.total_floors_spin.value(),
        )

    def export_pdf(self, filepath: str):
        """تصدير المخطط إلى PDF"""
        if not self.current_plan:
            raise ValueError("لا يوجد مخطط لتصديره")
        self.figure.savefig(
            filepath, format="pdf",
            facecolor="#0D1117", edgecolor="none",
            bbox_inches="tight", dpi=150,
        )
