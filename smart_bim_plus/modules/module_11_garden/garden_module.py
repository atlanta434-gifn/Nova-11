import json
from PyQt6.QtWidgets import QVBoxLayout, QComboBox, QLabel, QGroupBox, QFormLayout
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .garden_engine import GardenEngine

class GardenModule(BaseModule):
    """وحدة الحديقة الذكية — واجهة المستخدم والمخططات"""

    SYSTEM_NUMBER = 11
    SYSTEM_NAME = "Smart Garden"
    SYSTEM_NAME_AR = "الحديقة الذكية"
    ICON_NAME = "leaf"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        group_box = QGroupBox("إعدادات الحديقة")
        layout = QFormLayout()
        
        self.climate_combo = QComboBox()
        self.climate_combo.addItems(["جاف (arid)", "متوسطي (mediterranean)", "استوائي (tropical)"])
        
        self.style_combo = QComboBox()
        self.style_combo.addItems(["رسمي (formal)", "إنجليزي (english)", "ياباني (japanese)", "جاف (xeriscape)"])
        
        self.water_combo = QComboBox()
        self.water_combo.addItems(["مياه البلدية", "بئر", "مياه رمادية معالجة"])
        
        self.soil_combo = QComboBox()
        self.soil_combo.addItems(["طينية", "رملية", "طميية"])
        
        layout.addRow("المنطقة المناخية:", self.climate_combo)
        layout.addRow("نمط الحديقة:", self.style_combo)
        layout.addRow("مصدر المياه:", self.water_combo)
        layout.addRow("نوع التربة:", self.soil_combo)
        
        group_box.setLayout(layout)
        self.input_layout.insertWidget(1, group_box)

        self.summary_label = QLabel("الملخص سيظهر هنا بعد التوليد.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #C9D1D9; margin-top: 20px;")
        self.input_layout.insertWidget(2, self.summary_label)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
            
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد بيانات النظام"""
        engine = GardenEngine(self.building_data)
        
        climate_map = {0: "arid", 1: "mediterranean", 2: "tropical"}
        style_map = {0: "formal", 1: "english", 2: "japanese", 3: "xeriscape"}
        
        climate = climate_map.get(self.climate_combo.currentIndex(), "arid")
        style = style_map.get(self.style_combo.currentIndex(), "xeriscape")
        
        self.generated_data = engine.generate_system(climate, style)
        self._update_ui()
        self._draw_canvas()

    def _update_ui(self):
        """تحديث واجهة المستخدم بالنتائج"""
        data = self.generated_data
        plants = "، ".join(data['plants'])
        summary = (
            f"مساحة الحديقة: {data['garden_area']:.2f} م²\n"
            f"استهلاك المياه: {data['total_water_liters']:.2f} لتر/يوم\n"
            f"عدد الرشاشات: {len(data['sprinklers'])}\n"
            f"طول الأنابيب: {data['total_pipe_length']:.2f} م\n"
            f"قدرة المضخة: {data['pump_power_kw']:.2f} كيلوواط\n"
            f"سعة الخزان: {data['tank_capacity_liters']:.2f} لتر\n"
            f"النباتات المقترحة: {plants}\n"
            f"الجدولة: {data['schedule']}"
        )
        self.summary_label.setText(summary)

    def _draw_canvas(self):
        """رسم المخطط"""
        self.ax.clear()
        self.ax.set_facecolor("#161B22")
        self.ax.set_title("مخطط الحديقة الذكية والري", color="#C9D1D9")
        
        plot_w = self.building_data.get("plot_width", 30.0)
        plot_l = self.building_data.get("plot_length", 30.0)
        
        self.ax.add_patch(patches.Rectangle((0, 0), plot_w, plot_l, fill=True, color="#238636", alpha=0.3, label="الحديقة"))
        
        for r in self.building_data.get("rooms", []):
            rx = float(r.get("position_x", 0))
            ry = float(r.get("position_y", 0))
            rw = float(r.get("width", 0))
            rl = float(r.get("length", 0))
            self.ax.add_patch(patches.Rectangle((rx, ry), rw, rl, fill=True, color="#8B949E", label="المبنى"))

        data = self.generated_data
        radius = data.get("sprinkler_radius", 3.0)
        
        for sx, sy in data.get("sprinklers", []):
            self.ax.add_patch(patches.Circle((sx, sy), radius, fill=True, color="#58A6FF", alpha=0.2))
            self.ax.plot(sx, sy, marker='o', color="#58A6FF", markersize=4)
            
        for p1, p2 in data.get("pipes", []):
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#58A6FF", linewidth=2, alpha=0.8)

        self.ax.plot(0, 0, marker='s', color="#3FB950", markersize=8, label="مصدر المياه")
        
        self.ax.set_xlim(-2, plot_w + 2)
        self.ax.set_ylim(-2, plot_l + 2)
        self.ax.set_aspect('equal')
        
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='upper right', facecolor="#0D1117", edgecolor="#C9D1D9", labelcolor="#C9D1D9")
        
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
