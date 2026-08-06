import numpy as np
from PyQt6.QtWidgets import (QComboBox, QFormLayout, QTextEdit)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .acoustics_engine import AcousticsEngine

class AcousticsModule(BaseModule):
    """وحدة الصوتيات والترفيه"""

    SYSTEM_NUMBER = 17
    SYSTEM_NAME = "Acoustics & Entertainment"
    SYSTEM_NAME_AR = "الصوتيات والترفيه"
    ICON_NAME = "speaker"

    def __init__(self, parent=None):
        self.engine = AcousticsEngine()
        super().__init__(parent)

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        layout = QFormLayout()
        
        self.room_combo = QComboBox()
        layout.addRow("الغرفة:", self.room_combo)

        self.room_type_combo = QComboBox()
        self.room_type_combo.addItems(["سينما منزلية", "غرفة موسيقى", "غرفة معيشة"])
        layout.addRow("نوع الغرفة:", self.room_type_combo)
        
        self.system_combo = QComboBox()
        self.system_combo.addItems(["5.1", "7.1", "Atmos"])
        layout.addRow("النظام الصوتي:", self.system_combo)

        self.wall_mat_combo = QComboBox()
        self.wall_mat_combo.addItems(["خرسانة", "جدران جافة", "ألواح صوتية", "خشب"])
        layout.addRow("مادة الجدران:", self.wall_mat_combo)

        self.floor_mat_combo = QComboBox()
        self.floor_mat_combo.addItems(["خرسانة", "سجاد", "خشب"])
        layout.addRow("مادة الأرضية:", self.floor_mat_combo)

        self.ceil_mat_combo = QComboBox()
        self.ceil_mat_combo.addItems(["خرسانة", "جدران جافة", "ألواح صوتية"])
        layout.addRow("مادة السقف:", self.ceil_mat_combo)

        self.input_layout.insertLayout(1, layout)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.input_layout.insertWidget(2, self.summary_text)

    def set_building_data(self, data: dict):
        """تعيين بيانات المبنى وتحديث القوائم"""
        super().set_building_data(data)
        self.room_combo.clear()
        if "rooms" in data:
            for room in data["rooms"]:
                self.room_combo.addItem(room.get("name", "غرفة غير مسماة"), room)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد بيانات النظام"""
        room_data = self.room_combo.currentData()
        if not room_data:
            raise ValueError("لم يتم تحديد غرفة")

        width = float(room_data.get("width", 5.0))
        length = float(room_data.get("length", 4.0))
        height = 3.0 

        wall_mat = self.wall_mat_combo.currentText()
        floor_mat = self.floor_mat_combo.currentText()
        ceil_mat = self.ceil_mat_combo.currentText()
        sys_type = self.system_combo.currentText()
        room_type = self.room_type_combo.currentText()

        rt60 = self.engine.calculate_rt60(width, length, height, wall_mat, floor_mat, ceil_mat)
        source_pos = (width / 2, length * 0.1)
        
        rays = self.engine.ray_tracing(width, length, source_pos, wall_mat)
        spl, xc, yc = self.engine.calculate_spl_grid(width, length, source_pos)
        speakers = self.engine.optimize_speaker_placement(width, length, sys_type)
        stc = self.engine.stc_ratings.get(wall_mat, 35)

        summary = f"زمن الرنين (RT60): {rt60:.2f} ثانية\n"
        summary += f"معدل انتقال الصوت (STC): {stc} ديسيبل\n"
        summary += f"عدد السماعات المقترحة: {len(speakers)}\n"
        
        target_rt60 = 0.3 if room_type == "سينما منزلية" else (0.8 if room_type == "غرفة موسيقى" else 0.5)
        if rt60 > target_rt60 + 0.1:
            summary += "توصية: إضافة ألواح صوتية لتقليل زمن الرنين.\n"
        elif rt60 < target_rt60 - 0.1:
            summary += "توصية: تقليل المواد الممتصة للصوت.\n"
            
        self.summary_text.setText(summary)

        self.ax.clear()
        self.ax.set_facecolor("#161B22")
        self.ax.set_title(f"تحليل الصوتيات: {room_data.get('name', '')}", color="#C9D1D9")
        
        extent = [0, width, 0, length]
        self.ax.imshow(spl.T, extent=extent, origin='lower', cmap='inferno', alpha=0.5)
        
        self.ax.add_patch(patches.Rectangle((0, 0), width, length, fill=False, color="#58A6FF", lw=2))

        for path in rays:
            xs, ys = zip(*path)
            self.ax.plot(xs, ys, color="#D29922", alpha=0.1, lw=0.5)

        for spk in speakers:
            x, y, name = spk
            self.ax.plot(x, y, 's', color="#3FB950", markersize=8)
            self.ax.text(x, y + 0.2, name, color="#C9D1D9", fontsize=8, ha='center')

        self.ax.set_xlim(-1, width + 1)
        self.ax.set_ylim(-1, length + 1)
        self.ax.set_aspect('equal')
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
            
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
