import math
import numpy as np
from typing import Dict, Any, Tuple

class PoolEngine:
    """محرك حسابات المسبح الذكي"""

    def __init__(self):
        """تهيئة محرك المسبح"""
        self.gravity = 9.81
        self.water_density = 1000.0

    def calculate_pool_dimensions(self, area: float, pool_type: str, depth_type: str) -> Dict[str, Any]:
        """حساب أبعاد المسبح بناءً على المساحة والنوع والعمق"""
        dimensions = {}
        if pool_type == "مستطيل":
            width = np.sqrt(area / 2.0)
            length = width * 2.0
            dimensions["width"] = width
            dimensions["length"] = length
        elif pool_type == "حرف L":
            width = np.sqrt(area / 3.0)
            length = width * 2.0
            dimensions["main_width"] = width
            dimensions["main_length"] = length
            dimensions["L_width"] = width
            dimensions["L_length"] = width
        elif pool_type in ["كلوي", "انفنيتي"]:
            width = np.sqrt(area / 1.5)
            length = width * 1.5
            dimensions["width"] = width
            dimensions["length"] = length
            dimensions["radius"] = width / 2.0
        else:
            width = np.sqrt(area)
            length = width
            dimensions["width"] = width
            dimensions["length"] = length
            
        if depth_type == "ضحل":
            avg_depth = 1.2
            min_depth, max_depth = 0.9, 1.5
        elif depth_type == "متوسط":
            avg_depth = 1.5
            min_depth, max_depth = 1.0, 2.0
        else:
            avg_depth = 2.0
            min_depth, max_depth = 1.2, 3.0
            
        dimensions["avg_depth"] = avg_depth
        dimensions["min_depth"] = min_depth
        dimensions["max_depth"] = max_depth
        dimensions["volume"] = area * avg_depth
        
        return dimensions

    def size_filtration_system(self, volume_m3: float) -> Dict[str, Any]:
        """تصميم نظام الفلترة والمضخة"""
        turnover_hours = 6.0
        flow_rate_m3h = volume_m3 / turnover_hours
        flow_rate_gpm = flow_rate_m3h * 4.40287
        
        filter_area_m2 = flow_rate_m3h / 40.0
        filter_diameter = 2 * np.sqrt(filter_area_m2 / np.pi)
        
        return {
            "turnover_rate_h": turnover_hours,
            "flow_rate_m3h": flow_rate_m3h,
            "flow_rate_gpm": flow_rate_gpm,
            "filter_area_m2": filter_area_m2,
            "filter_diameter_m": filter_diameter
        }

    def size_piping_system(self, flow_rate_gpm: float) -> Dict[str, Any]:
        """حساب أقطار الأنابيب باستخدام معادلة هازن-ويليامز"""
        c_factor = 140.0
        velocity_fps = 6.0
        
        area_in2 = (flow_rate_gpm * 0.3208) / velocity_fps
        diameter_in = 2 * np.sqrt(area_in2 / np.pi)
        diameter_mm = diameter_in * 25.4
        
        standard_sizes = [32, 40, 50, 63, 75, 90, 110, 160]
        selected_size = next((s for s in standard_sizes if s >= diameter_mm), standard_sizes[-1])
        
        return {
            "calculated_diameter_mm": diameter_mm,
            "selected_diameter_mm": selected_size,
            "velocity_fps": velocity_fps
        }

    def calculate_heating_system(self, area: float, volume: float, heating_type: str, cover_type: str) -> Dict[str, Any]:
        """حساب متطلبات التسخين وفقد الحرارة"""
        temp_diff_c = 10.0
        evaporation_loss = 200.0 * area
        radiation_loss = 100.0 * area
        convection_loss = 50.0 * area
        
        if cover_type != "بدون غطاء":
            evaporation_loss *= 0.2
            radiation_loss *= 0.5
            convection_loss *= 0.3
            
        total_heat_loss_watts = evaporation_loss + radiation_loss + convection_loss
        heat_loss_btu = total_heat_loss_watts * 3.412
        
        heat_up_btu = (volume * 1000.0) * temp_diff_c * 1.0 * 3.968 / 24.0
        required_heater_btu = max(heat_loss_btu, heat_up_btu) * 1.2
        
        return {
            "heat_loss_btu": heat_loss_btu,
            "required_heater_btu": required_heater_btu,
            "heating_type": heating_type
        }

    def calculate_chemical_system(self, volume: float) -> Dict[str, Any]:
        """حساب المتطلبات الكيميائية للمسبح"""
        chlorine_dose_ppm = 2.0
        chlorine_daily_grams = (volume * 1000.0) * (chlorine_dose_ppm / 1000.0)
        
        return {
            "target_ph": 7.4,
            "target_alkalinity_ppm": 100.0,
            "chlorine_daily_grams": chlorine_daily_grams,
            "salt_required_kg": volume * 4.0 if volume > 0 else 0
        }

    def calculate_structural(self, max_depth: float) -> Dict[str, Any]:
        """حسابات إنشائية لجدران المسبح"""
        max_hydrostatic_pressure = self.water_density * self.gravity * max_depth
        wall_thickness_m = max(0.20, max_depth * 0.15)
        rebar_ratio = 0.0025
        
        return {
            "max_pressure_kpa": max_hydrostatic_pressure / 1000.0,
            "wall_thickness_m": wall_thickness_m,
            "rebar_ratio": rebar_ratio
        }

    def estimate_energy_cost(self, pump_gpm: float, heater_btu: float) -> Dict[str, Any]:
        """تقدير تكاليف التشغيل السنوية"""
        pump_kw = (pump_gpm * 0.746) / 3960.0 * 10.0 
        pump_annual_kwh = pump_kw * 8.0 * 365.0
        
        heater_kw = heater_btu / 3412.0
        heater_annual_kwh = heater_kw * 4.0 * 150.0 
        
        cost_per_kwh = 0.30
        
        return {
            "pump_annual_cost": pump_annual_kwh * cost_per_kwh,
            "heater_annual_cost": heater_annual_kwh * cost_per_kwh,
            "total_annual_cost": (pump_annual_kwh + heater_annual_kwh) * cost_per_kwh
        }

    def run_full_analysis(self, area: float, pool_type: str, depth_type: str, heating_type: str, cover_type: str) -> Dict[str, Any]:
        """تنفيذ التحليل الشامل للمسبح"""
        dims = self.calculate_pool_dimensions(area, pool_type, depth_type)
        vol = dims["volume"]
        
        filtration = self.size_filtration_system(vol)
        piping = self.size_piping_system(filtration["flow_rate_gpm"])
        heating = self.calculate_heating_system(area, vol, heating_type, cover_type)
        chemical = self.calculate_chemical_system(vol)
        structural = self.calculate_structural(dims["max_depth"])
        costs = self.estimate_energy_cost(filtration["flow_rate_gpm"], heating["required_heater_btu"])
        
        return {
            "dimensions": dims,
            "filtration": filtration,
            "piping": piping,
            "heating": heating,
            "chemical": chemical,
            "structural": structural,
            "costs": costs
        }
