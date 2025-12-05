import math

class MaterialManager:
    # --- GLOBAL BUILD SETTINGS ---
    PLACEMENT_MODE_HOLLOW = False # Toggled by H/J
    
    # --- BASE PROPERTIES (Tunable) ---
    # E: Stiffness/Young's Modulus approximation
    # Density: Mass per unit length
    # Strength: Breaking threshold
    MATERIALS = {
        "wood":   {"E": 1000.0, "density": 1.0, "strength": 0.015, "max_length": 20},
        "bamboo": {"E": 2000.0, "density": 0.5, "strength": 0.100, "max_length": None},
        "vine":   {"E": 100.0,  "density": 0.2, "strength": 0.300, "max_length": None}
    }
    
    # Agent Properties
    AGENT = {
        "mass": 5.0
    }

    # --- GEOMETRY CONSTANTS ---
    THICKNESS = 0.1 # 10cm Diameter
    WALL_THICKNESS = 0.01 # 1cm wall for hollow beams

    @staticmethod
    def get_hollow_factor():
        """
        Calculates the physical reduction ratio for a hollow tube 
        vs a solid cylinder of the same outer diameter.
        """
        R = MaterialManager.THICKNESS / 2.0
        r = R - MaterialManager.WALL_THICKNESS
        
        area_solid = math.pi * (R**2)
        area_hollow = math.pi * (R**2 - r**2)
        
        return area_hollow / area_solid

    @staticmethod
    def get_properties(mat_type, is_hollow):
        """Returns physical properties adjusted for geometry."""
        base = MaterialManager.MATERIALS.get(mat_type, MaterialManager.MATERIALS["wood"])
        
        factor = 1.0
        if is_hollow:
            factor = MaterialManager.get_hollow_factor()

        return {
            "E": base["E"] * factor,
            "density": base["density"] * factor,
            "strength": base["strength"] # Strength (Strain limit) usually doesn't change by geometry, only Stiffness does.
        }