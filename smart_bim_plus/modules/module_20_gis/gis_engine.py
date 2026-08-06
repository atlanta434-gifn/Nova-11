import numpy as np
from scipy.ndimage import gaussian_filter

class GISEngine:
    """محرك التحليل الجغرافي وحسابات الحفر والردم"""
    def __init__(self, plot_width: float, plot_length: float, resolution: float = 1.0):
        self.width = plot_width
        self.length = plot_length
        self.resolution = resolution
        self.nx = int(np.ceil(self.width / resolution))
        self.ny = int(np.ceil(self.length / resolution))
        self.X, self.Y = np.meshgrid(
            np.linspace(0, self.width, self.nx),
            np.linspace(0, self.length, self.ny)
        )
        self.elevation = None
        self.slope = None
        self.flow_dir = None

    def generate_synthetic_terrain(self, base_elevation: float = 100.0, variance: float = 5.0) -> np.ndarray:
        """توليد تضاريس اصطناعية باستخدام دالة التمويه"""
        np.random.seed(42)
        noise = np.random.normal(0, 1, (self.ny, self.nx))
        sigma_val = max(min(self.nx, self.ny) / 10, 1)
        smoothed = gaussian_filter(noise, sigma=sigma_val)
        min_val = smoothed.min()
        max_val = smoothed.max()
        if max_val > min_val:
            smoothed = (smoothed - min_val) / (max_val - min_val)
        self.elevation = base_elevation + smoothed * variance
        return self.elevation

    def analyze_slope(self) -> dict:
        """حساب الميول وتصنيفها"""
        dx = self.resolution
        dy = self.resolution
        dz_dx = np.gradient(self.elevation, dx, axis=1)
        dz_dy = np.gradient(self.elevation, dy, axis=0)
        slope_pct = np.sqrt(dz_dx**2 + dz_dy**2) * 100
        
        slope_class = np.zeros_like(slope_pct)
        slope_class[slope_pct > 5] = 1
        slope_class[slope_pct > 15] = 2
        slope_class[slope_pct > 30] = 3
        
        total_cells = slope_class.size
        self.slope = {
            'percentage': slope_pct,
            'classification': slope_class,
            'stats': {
                'flat': np.sum(slope_class == 0) / total_cells * 100,
                'moderate': np.sum(slope_class == 1) / total_cells * 100,
                'steep': np.sum(slope_class == 2) / total_cells * 100,
                'unstable': np.sum(slope_class == 3) / total_cells * 100
            }
        }
        return self.slope

    def calculate_cut_fill(self, target_grade: float) -> dict:
        """حساب كميات الحفر والردم بناءً على منسوب التسوية"""
        diff = self.elevation - target_grade
        cell_area = self.resolution ** 2
        
        cut_mask = diff > 0
        fill_mask = diff < 0
        
        cut_vol = float(np.sum(diff[cut_mask]) * cell_area)
        fill_vol = float(np.sum(-diff[fill_mask]) * cell_area)
        
        return {
            'cut_volume': cut_vol,
            'fill_volume': fill_vol,
            'net': cut_vol - fill_vol,
            'cut_mask': cut_mask,
            'fill_mask': fill_mask,
            'diff': diff
        }

    def analyze_drainage(self) -> dict:
        """تحليل مسارات تصريف المياه"""
        pad_z = np.pad(self.elevation, 1, mode='edge')
        dx = [1, 1, 0, -1, -1, -1, 0, 1]
        dy = [0, 1, 1, 1, 0, -1, -1, -1]
        
        drop = np.zeros((self.ny, self.nx, 8))
        for i in range(8):
            drop[:, :, i] = self.elevation - pad_z[1+dy[i]:self.ny+1+dy[i], 1+dx[i]:self.nx+1+dx[i]]
            
        flow_dir_idx = np.argmax(drop, axis=2)
        u = np.zeros_like(self.elevation)
        v = np.zeros_like(self.elevation)
        
        for i in range(8):
            mask = flow_dir_idx == i
            u[mask] = dx[i]
            v[mask] = dy[i]
            
        self.flow_dir = {'u': u, 'v': v}
        return self.flow_dir

    def get_optimal_grade(self) -> float:
        """حساب منسوب التسوية الأمثل لموازنة الحفر والردم"""
        return float(np.mean(self.elevation))
