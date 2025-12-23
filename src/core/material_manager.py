import math

class MaterialManager:
    # --- GLOBAL SETTINGS (Saved/Loaded) ---
    SETTINGS = {
        "base_temp": 25.0,     # Construction temperature (°C)
        "sim_temp": 25.0       # Current Simulation temperature (°C)
    }
    
    # --- PHYSICAL CONSTANTS ---
    MATERIALS = {
        "wood":   {
            "E": 11e9,          # 11 GPa
            "density": 600.0,   # 600 kg/m^3
            "strength": 40e6,   # 40 MPa
            "alpha": 5e-6,      
            "thickness": 0.20,  # 20 cm
            "hollow_ratio": 0.0 
        },
        "bamboo": {
            "E": 18e9,          
            "density": 700.0,   
            "strength": 60e6,   
            "alpha": 10e-6,     
            "thickness": 0.15, 
            "hollow_ratio": 0.0
        },
        "vine":   {
            "E": 0.5e9,         
            "density": 400.0,   
            "strength": 20e6,   
            "alpha": 2e-6,      
            "thickness": 0.05,
            "hollow_ratio": 0.0
        },
        "steel": {
            "E": 200e9,         # 200 GPa
            "density": 7850.0,  
            "strength": 250e6,  # 250 MPa
            "alpha": 12e-6,
            "thickness": 0.05,  # 5cm thick beams
            "hollow_ratio": 0.0
        },
        "cable": {
            "E": 160e9,         # 160 GPa
            "density": 7850.0,
            "strength": 1000e6, # 1000 MPa
            "alpha": 12e-6,
            "thickness": 0.02,  # 2cm thick
            "hollow_ratio": 0.0
        },
        "spaghetti": {
            "E": 3e9,           # 3 GPa
            "density": 1500.0,
            "strength": 10e6,   # 10 MPa
            "alpha": 0.0,       
            "thickness": 0.03,  
            "hollow_ratio": 0.0
        }
    }
    
    AGENT = {
        "mass": 70.0, 
        "speed": 5.0
    }

    @staticmethod
    def get_geometry(thickness, hollow_ratio):
        """Calculates Area (A) and Inertia (I) based on hollow ratio."""
        R = thickness / 2.0
        ratio = max(0.0, min(0.99, hollow_ratio))
        r = R * ratio
        
        area = math.pi * (R**2 - r**2)
        inertia = (math.pi / 4.0) * (R**4 - r**4)
            
        return area, inertia

    @staticmethod
    def get_properties(mat_type, hollow_ratio=None):
        base = MaterialManager.MATERIALS.get(mat_type, MaterialManager.MATERIALS["wood"])
        
        if hollow_ratio is None:
            hollow_ratio = base.get("hollow_ratio", 0.0)
            
        thickness = base.get("thickness", 0.1)
        area, inertia = MaterialManager.get_geometry(thickness, hollow_ratio)
        
        return {
            "E": base["E"],
            "density": base["density"], 
            "strength": base["strength"],
            "alpha": base["alpha"],
            "thickness": thickness,
            "area": area,
            "inertia": inertia
        }