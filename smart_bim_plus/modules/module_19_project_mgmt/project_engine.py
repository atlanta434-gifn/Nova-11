import numpy as np
from typing import Dict, List, Any, Tuple

class Activity:
    """صنف يمثل نشاط في المشروع"""
    def __init__(self, id: str, name: str, min_dur: float, likely_dur: float, max_dur: float, cost_rate: float):
        self.id = id
        self.name = name
        self.min_dur = min_dur
        self.likely_dur = likely_dur
        self.max_dur = max_dur
        self.cost_rate = cost_rate
        self.predecessors: List[str] = []
        self.successors: List[str] = []
        
        self.duration = likely_dur
        self.es = 0.0
        self.ef = 0.0
        self.ls = 0.0
        self.lf = 0.0
        self.tf = 0.0
        self.ff = 0.0
        self.is_critical = False

class ProjectEngine:
    """محرك حسابات إدارة المشاريع والمسار الحرج"""
    def __init__(self, building_data: Dict[str, Any]):
        self.building_data = building_data
        self.activities: Dict[str, Activity] = {}
        self.project_duration = 0.0
        self.p50 = 0.0
        self.p90 = 0.0
        self.total_cost = 0.0
        self.s_curve: List[Tuple[float, float]] = []
        self._initialize_activities()
        
    def _initialize_activities(self):
        """تهيئة الأنشطة بناء على بيانات المبنى"""
        total_area = sum([r.get("area", 0) for r in self.building_data.get("rooms", [])])
        floors = self.building_data.get("total_floors", 1)
        if total_area == 0:
            total_area = 1000
            
        area_factor = total_area / 1000.0
        floor_factor = floors / 2.0
        factor = area_factor * floor_factor
        
        acts_data = [
            ("A1", "التصميم المعماري", 10, 15, 25, 500),
            ("A2", "تجهيز الموقع", 5, 7, 10, 1000),
            ("A3", "الأساسات", 15, 20, 30, 2000),
            ("A4", "الهيكل الخرساني", 20, 30, 60, 3000),
            ("A5", "الأسقف", 10, 15, 25, 1500),
            ("A6", "أعمال البناء", 15, 20, 30, 800),
            ("A7", "السباكة", 10, 12, 15, 600),
            ("A8", "الكهرباء", 10, 15, 20, 700),
            ("A9", "التكييف", 15, 20, 25, 1200),
            ("A10", "مكافحة الحريق", 7, 10, 15, 900),
            ("A11", "الاتصالات", 5, 8, 12, 400),
            ("A12", "أنظمة الأمان", 5, 7, 10, 500),
            ("A13", "المصاعد", 10, 15, 20, 2500),
            ("A14", "الأبواب والنوافذ", 10, 14, 20, 800),
            ("A15", "التشطيبات الخارجية", 15, 20, 30, 1000),
            ("A16", "التشطيبات الداخلية", 20, 30, 45, 1200),
            ("A17", "الأسطح والعزل", 7, 10, 15, 700),
            ("A18", "تنسيق الموقع", 10, 15, 20, 600),
            ("A19", "الاختبار والتشغيل", 7, 10, 15, 800),
            ("A20", "التسليم", 3, 5, 7, 200)
        ]
        
        for d in acts_data:
            act = Activity(
                d[0], d[1], 
                d[2] * factor, d[3] * factor, d[4] * factor, 
                d[5]
            )
            self.activities[d[0]] = act
            
        deps = [
            ("A1", "A2"), ("A2", "A3"), ("A3", "A4"), ("A4", "A5"),
            ("A5", "A6"), ("A6", "A7"), ("A6", "A8"), ("A6", "A9"),
            ("A6", "A10"), ("A7", "A11"), ("A8", "A11"), ("A9", "A11"),
            ("A10", "A11"), ("A11", "A12"), ("A12", "A13"), ("A6", "A14"),
            ("A14", "A15"), ("A14", "A16"), ("A5", "A17"), ("A15", "A18"),
            ("A16", "A18"), ("A17", "A18"), ("A13", "A18"), ("A18", "A19"),
            ("A19", "A20")
        ]
        
        for pred, succ in deps:
            if pred in self.activities and succ in self.activities:
                self.activities[pred].successors.append(succ)
                self.activities[succ].predecessors.append(pred)
                
    def calculate_cpm(self):
        """حساب المسار الحرج"""
        for act in self.activities.values():
            act.duration = round(act.likely_dur, 1)
            
        start_nodes = [a for a in self.activities.values() if not a.predecessors]
        queue = start_nodes.copy()
        processed = set()
        
        while queue:
            curr = queue.pop(0)
            if curr.id in processed:
                continue
                
            ready = True
            max_ef = 0.0
            for p_id in curr.predecessors:
                if p_id not in processed:
                    ready = False
                    break
                max_ef = max(max_ef, self.activities[p_id].ef)
                
            if ready:
                curr.es = max_ef
                curr.ef = curr.es + curr.duration
                processed.add(curr.id)
                for s_id in curr.successors:
                    if s_id not in queue:
                        queue.append(self.activities[s_id])
            else:
                queue.append(curr)
                
        self.project_duration = max(a.ef for a in self.activities.values())
        
        end_nodes = [a for a in self.activities.values() if not a.successors]
        for a in end_nodes:
            a.lf = self.project_duration
            a.ls = a.lf - a.duration
            
        queue = end_nodes.copy()
        processed_bw = set()
        
        while queue:
            curr = queue.pop(0)
            if curr.id in processed_bw:
                continue
                
            ready = True
            min_ls = self.project_duration
            for s_id in curr.successors:
                if s_id not in processed_bw:
                    ready = False
                    break
                min_ls = min(min_ls, self.activities[s_id].ls)
                
            if ready:
                if curr.successors:
                    curr.lf = min_ls
                    curr.ls = curr.lf - curr.duration
                processed_bw.add(curr.id)
                for p_id in curr.predecessors:
                    if p_id not in queue:
                        queue.append(self.activities[p_id])
            else:
                queue.append(curr)
                
        for act in self.activities.values():
            act.tf = act.ls - act.es
            min_succ_es = min([self.activities[s].es for s in act.successors], default=act.ef)
            act.ff = min_succ_es - act.ef
            if abs(act.tf) < 0.1:
                act.is_critical = True
                
        self.calculate_costs()
        
    def calculate_costs(self):
        """حساب التكاليف والتدفق النقدي"""
        self.total_cost = 0.0
        daily_costs = np.zeros(int(np.ceil(self.project_duration)) + 1)
        
        for act in self.activities.values():
            act_cost = act.duration * act.cost_rate
            self.total_cost += act_cost
            if act.duration > 0:
                daily_rate = act_cost / act.duration
                start_day = int(np.floor(act.es))
                end_day = int(np.ceil(act.ef))
                for day in range(start_day, end_day):
                    if day < len(daily_costs):
                        daily_costs[day] += daily_rate
                        
        cum_cost = 0.0
        self.s_curve = []
        for i, cost in enumerate(daily_costs):
            cum_cost += cost
            self.s_curve.append((float(i), cum_cost))
            
    def run_monte_carlo(self, iterations: int = 1000):
        """تحليل المخاطر باستخدام محاكاة مونت كارلو"""
        results = []
        
        ordered_keys = []
        queue = [k for k, v in self.activities.items() if not v.predecessors]
        processed = set()
        
        while queue:
            curr = queue.pop(0)
            if curr in processed:
                continue
                
            ready = True
            for p in self.activities[curr].predecessors:
                if p not in processed:
                    ready = False
                    break
            if ready:
                ordered_keys.append(curr)
                processed.add(curr)
                queue.extend(self.activities[curr].successors)
            else:
                queue.append(curr)
                
        for _ in range(iterations):
            durations = {}
            for k in ordered_keys:
                a = self.activities[k]
                d = np.random.triangular(a.min_dur, a.likely_dur, a.max_dur)
                durations[k] = d
                
            efs = {}
            for k in ordered_keys:
                a = self.activities[k]
                max_ef = 0.0
                for p in a.predecessors:
                    max_ef = max(max_ef, efs[p])
                efs[k] = max_ef + durations[k]
                
            proj_dur = max(efs.values()) if efs else 0.0
            results.append(proj_dur)
            
        if results:
            results.sort()
            self.p50 = results[int(len(results) * 0.5)]
            self.p90 = results[int(len(results) * 0.9)]
