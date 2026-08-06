import numpy as np
from typing import Dict, Any, Tuple

class EnergyEngine:
    """محرك حسابات وإدارة الطاقة والتحسين باستخدام البرمجة الخطية"""

    def __init__(self, building_data: Dict[str, Any]):
        self.building_data = building_data
        self.area = sum(r.get('area', 0) for r in self.building_data.get('rooms', []))
        if self.area == 0:
            self.area = self.building_data.get('plot_width', 10) * self.building_data.get('plot_length', 10)

    def calculate_base_loads(self, pattern: str) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
        """حساب أحمال الاستهلاك الأساسية"""
        hours = np.arange(24)
        
        hvac_base = 0.4 * self.area
        lighting_base = 0.15 * self.area
        appliances_base = 0.2 * self.area
        water_base = 0.15 * self.area
        cooking_base = 0.1 * self.area

        categories = {
            "HVAC": hvac_base * 24,
            "Lighting": lighting_base * 24,
            "Appliances": appliances_base * 24,
            "Hot Water": water_base * 24,
            "Cooking": cooking_base * 24
        }

        if pattern == "سكني":
            critical_profile = np.array([0.3, 0.2, 0.2, 0.2, 0.3, 0.5, 0.8, 0.9, 0.6, 0.5, 0.5, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.3, 1.2, 1.0, 0.8, 0.6, 0.4])
            shiftable_profile = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.3, 0.5, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.7, 0.8, 0.9, 1.0, 1.0, 0.8, 0.6, 0.5, 0.4, 0.2, 0.1])
        else:
            critical_profile = np.array([0.2, 0.2, 0.2, 0.2, 0.3, 0.4, 0.7, 1.0, 1.2, 1.3, 1.3, 1.3, 1.3, 1.3, 1.2, 1.1, 1.0, 0.8, 0.6, 0.4, 0.3, 0.3, 0.2, 0.2])
            shiftable_profile = np.array([0.1, 0.1, 0.1, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1])

        critical_load = critical_profile * (hvac_base + lighting_base + appliances_base * 0.5)
        shiftable_load = shiftable_profile * (water_base + cooking_base + appliances_base * 0.5)

        return critical_load, shiftable_load, categories

    def calculate_solar_production(self, panel_wattage: float, hours: np.ndarray) -> np.ndarray:
        """حساب إنتاج الطاقة الشمسية"""
        peak_irradiance = 1.0
        solar_profile = np.maximum(0, np.sin(np.pi * (hours - 6) / 12))
        solar_profile[:6] = 0
        solar_profile[18:] = 0
        
        num_panels = max(10, int(self.area / 10))
        efficiency = 0.18
        area_per_panel = 1.6
        
        total_production = solar_profile * peak_irradiance * num_panels * area_per_panel * efficiency * 1000 / 1000.0
        return total_production

    def optimize_load_scheduling(self, critical_load: np.ndarray, shiftable_load: np.ndarray, solar_prod: np.ndarray, tariff: float, has_battery: bool) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """تحسين جدول الأحمال لتعظيم الاستفادة من الطاقة الشمسية"""
        total_shiftable = np.sum(shiftable_load)
        
        optimized_shiftable = np.zeros(24)
        
        net_load_before = critical_load - solar_prod
        
        hours_sorted_by_solar = np.argsort(net_load_before)
        
        remaining = total_shiftable
        for h in hours_sorted_by_solar:
            if net_load_before[h] < 0:
                capacity = -net_load_before[h]
                allocation = min(remaining, capacity)
                optimized_shiftable[h] += allocation
                remaining -= allocation
                
        if remaining > 0:
            avg_allocation = remaining / 24.0
            optimized_shiftable += avg_allocation
            
        final_load = critical_load + optimized_shiftable
        net_grid = final_load - solar_prod
        
        battery_charge = np.zeros(24)
        if has_battery:
            battery_cap = 10.0
            current_charge = 0.0
            for h in range(24):
                if net_grid[h] < 0:
                    charge_amount = min(battery_cap - current_charge, -net_grid[h])
                    current_charge += charge_amount
                    net_grid[h] += charge_amount
                elif net_grid[h] > 0 and current_charge > 0:
                    discharge_amount = min(current_charge, net_grid[h])
                    current_charge -= discharge_amount
                    net_grid[h] -= discharge_amount
                    
        import_energy = np.sum(np.maximum(0, net_grid))
        export_energy = np.sum(np.maximum(0, -net_grid))
        
        cost_with_solar = import_energy * tariff - export_energy * (tariff * 0.5)
        cost_without_solar = np.sum(critical_load + shiftable_load) * tariff
        
        return optimized_shiftable, net_grid, cost_without_solar, cost_with_solar

    def calculate_metrics(self, total_annual_kwh: float) -> Tuple[float, str]:
        """حساب مؤشرات الأداء والتقييم"""
        epi = total_annual_kwh / self.area
        if epi < 50:
            rating = "A++"
        elif epi < 100:
            rating = "A+"
        elif epi < 150:
            rating = "A"
        elif epi < 200:
            rating = "B"
        elif epi < 250:
            rating = "C"
        elif epi < 300:
            rating = "D"
        else:
            rating = "F"
        return epi, rating

    def calculate_roi(self, monthly_savings: float, panel_wattage: float, has_battery: bool) -> float:
        """حساب العائد على الاستثمار"""
        num_panels = max(10, int(self.area / 10))
        panel_cost = num_panels * panel_wattage * 1.5
        inverter_cost = 2000
        battery_cost = 5000 if has_battery else 0
        total_cost = panel_cost + inverter_cost + battery_cost
        
        annual_savings = monthly_savings * 12
        return total_cost / annual_savings if annual_savings > 0 else 999.0

