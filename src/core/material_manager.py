import math

class MaterialManager:
    # --- GLOBAL BUILD SETTINGS ---
    PLACEMENT_MODE_HOLLOW = False # Toggled by H/J
    
    # --- BASE PROPERTIES (Tunable) ---
    # E: Stiffness factor (for default thickness)
    # Density: Linear Density (kg/m) (for default thickness)
    # Strength: Breaking threshold
    # Thickness: Diameter of the beam in meters
    MATERIALS = {
        "wood":   {"E": 1000.0, "density": 1.0, "strength": 0.015, "max_length": 20, "thickness": 0.1},
        "bamboo": {"E": 2000.0, "density": 0.5, "strength": 0.100, "max_length": None, "thickness": 0.1},
        "vine":   {"E": 100.0,  "density": 0.2, "strength": 0.300, "max_length": None, "thickness": 0.05}
    }
    
    # Agent Properties
    AGENT = {
        "mass": 5.0,
        "speed": 5.0
    }

    # --- GEOMETRY CONSTANTS ---
    DEFAULT_THICKNESS = 0.1 # Reference for scaling
    WALL_THICKNESS = 0.01 # 1cm wall for hollow beams

    @staticmethod
    def get_area_properties(thickness, is_hollow):
        # Calculate Cross-Sectional Area
        R = thickness / 2.0
        area = math.pi * (R**2)
        
        if is_hollow:
            r = max(0, R - MaterialManager.WALL_THICKNESS)
            area_hollow = math.pi * (R**2 - r**2)
            return area_hollow
        
        return area

    @staticmethod
    def get_properties(mat_type, is_hollow):
        """Returns physical properties adjusted for geometry."""
        base = MaterialManager.MATERIALS.get(mat_type, MaterialManager.MATERIALS["wood"])
        
        # Current Configuration
        thickness = base.get("thickness", 0.1)
        
        # 1. Calculate Areas
        # Reference Area (Solid, Default Thickness) - used to normalize base values
        ref_R = MaterialManager.DEFAULT_THICKNESS / 2.0
        ref_area = math.pi * (ref_R**2)
        
        # Actual Area
        actual_area = MaterialManager.get_area_properties(thickness, is_hollow)
        
        # 2. Scale Factor
        # Properties (E, Density) scale with Area
        scale = actual_area / ref_area
        
        return {
            "E": base["E"] * scale,
            "density": base["density"] * scale, # Linear Density scales with area
            "strength": base["strength"],       # Strength (Material Limit) is constant
            "thickness": thickness
        }