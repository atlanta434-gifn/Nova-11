import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, PathPatch
from matplotlib.path import Path
from typing import Dict, Any, List


class DiagramGenerator:
    """مولد المخطط الخطي الفردي (Single Line Diagram)"""

    def __init__(self):
        self.figure = None
        self.ax = None

    def generate(self, electrical_data: Dict[str, Any],
                 figure_obj: plt.Figure) -> plt.Figure:
        """توليد المخطط ورسمه على الـ Figure الممرر"""
        self.figure = figure_obj
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.axis("off")

        main_breaker = electrical_data.get("main_breaker_amp", 63)
        circuits = electrical_data.get("circuits_data", {}).get("circuits", [])
        solar_capacity = electrical_data.get("solar_capacity_watt", 0)

        self._draw_main_panel(0, 10, main_breaker, solar_capacity > 0)

        start_x = -10
        y_pos = 5
        spacing = max(3, 20 / max(1, len(circuits)))

        for i, circuit in enumerate(circuits):
            x = start_x + (i * spacing)
            self._draw_circuit(x, y_pos, circuit)
            self._draw_connection(0, 8.5, x, y_pos + 1.5)

        self.ax.set_xlim(-15, 15)
        self.ax.set_ylim(-5, 15)
        self.figure.tight_layout()
        return self.figure

    def _draw_main_panel(self, x: float, y: float, amp: int, has_solar: bool):
        rect = Rectangle((x - 2, y - 1.5), 4, 3, facecolor="#30363D",
                         edgecolor="#58A6FF", linewidth=2)
        self.ax.add_patch(rect)
        self.ax.text(x, y + 0.5, "MAIN PANEL", color="#FFFFFF",
                     ha="center", va="center", fontweight="bold")
        self.ax.text(x, y - 0.5, f"Mcb {amp}A", color="#8B949E",
                     ha="center", va="center")

        if has_solar:
            self._draw_solar_inverter(x + 4, y)
            self.ax.plot([x + 2, x + 3], [y, y], color="#3FB950",
                         linewidth=2, linestyle="--")

    def _draw_solar_inverter(self, x: float, y: float):
        rect = Rectangle((x, y - 1), 2, 2, facecolor="#21262D",
                         edgecolor="#3FB950", linewidth=1.5)
        self.ax.add_patch(rect)
        self.ax.text(x + 1, y + 0.3, "INV", color="#3FB950",
                     ha="center", va="center", fontweight="bold")
        self.ax.text(x + 1, y - 0.3, "DC/AC", color="#8B949E",
                     ha="center", va="center", fontsize=8)

    def _draw_circuit(self, x: float, y: float, circuit: Dict):
        cb_amp = circuit.get("breaker", 16)
        wire = circuit.get("wire_mm2", 2.5)
        ctype = circuit.get("type", "mixed")
        rooms = ", ".join(circuit.get("rooms", [])[:2])
        if len(circuit.get("rooms", [])) > 2:
            rooms += ", ..."

        self.ax.plot([x, x], [y, y + 1.5], color="#C9D1D9", linewidth=1.5)
        self.ax.plot([x - 0.2, x + 0.2], [y + 1, y + 1],
                     color="#C9D1D9", linewidth=2)
        self.ax.text(x + 0.3, y + 1, f"CB {cb_amp}A", color="#58A6FF",
                     va="center", fontsize=9)

        self.ax.text(x + 0.3, y + 0.5, f"{wire}mm²", color="#8B949E",
                     va="center", fontsize=8)

        color = "#F85149" if ctype == "dedicated" else "#D29922"
        circ = Circle((x, y), 0.3, facecolor="none", edgecolor=color,
                      linewidth=1.5)
        self.ax.add_patch(circ)
        self.ax.text(x, y - 1, rooms, color="#C9D1D9",
                     ha="center", va="top", fontsize=8, rotation=45)

    def _draw_connection(self, x1: float, y1: float, x2: float, y2: float):
        self.ax.plot([x1, x1], [y1, y1 - 0.5], color="#58A6FF", linewidth=2)
        self.ax.plot([x1, x2], [y1 - 0.5, y1 - 0.5], color="#58A6FF", linewidth=2)
        self.ax.plot([x2, x2], [y1 - 0.5, y2], color="#58A6FF", linewidth=2)
