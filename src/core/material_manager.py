import math

class MaterialManager:
    # --- JÁTÉKMENET BEÁLLÍTÁSOK ---
    PLACEMENT_MODE_HOLLOW = False 
    
    # --- FIZIKAI AXIÓMÁK (Alapértékek) ---
    # Ezek a valós világban mért átlagos értékek.
    # E (Young-modulus): Mennyire merev az anyag (Pa).
    # Density: Sűrűség (kg/m³).
    # Strength: Szakítószilárdság (Pa) - Mekkora belső feszültségnél törik.
    # Alpha: Hőtágulási együttható (1/°C).
    MATERIALS = {
        "wood":   {
            "E": 11e9,          # 11 GPa (Normál fa)
            "density": 600.0,   # 600 kg/m³
            "strength": 40e6,   # 40 MPa
            "alpha": 5e-6,      
            "thickness": 0.20,  # 20 cm átmérő
        },
        "bamboo": {
            "E": 18e9,          # 18 GPa (Merevebb, mint a fa)
            "density": 700.0,   # 700 kg/m³ (Az anyaga sűrű, de csőként könnyű)
            "strength": 60e6,   # 60 MPa (Erősebb)
            "alpha": 10e-6,     
            "thickness": 0.15,  # 15 cm
        },
        "vine":   {
            "E": 0.5e9,         # 0.5 GPa (Nagyon rugalmas/nyúlós)
            "density": 400.0,   # 400 kg/m³
            "strength": 20e6,   # 20 MPa (Gyengébb)
            "alpha": 2e-6,      
            "thickness": 0.05,  # 5 cm
        }
    }
    
    AGENT = {
        "mass": 70.0, # Ixchel tömege (kg)
        "speed": 5.0
    }

    # --- GEOMETRIA ---
    WALL_THICKNESS = 0.02 # 2cm falvastagság csövek esetén

    @staticmethod
    def get_geometry(thickness, is_hollow):
        """Kiszámolja a Keresztmetszetet (A) és az Inerciát (I)."""
        R = thickness / 2.0
        
        if is_hollow:
            r = max(0, R - MaterialManager.WALL_THICKNESS)
            area = math.pi * (R**2 - r**2)
            # Üreges henger inerciája
            inertia = (math.pi / 4.0) * (R**4 - r**4)
        else:
            area = math.pi * (R**2)
            # Tömör henger inerciája
            inertia = (math.pi / 4.0) * (R**4)
            
        return area, inertia

    @staticmethod
    def get_properties(mat_type, is_hollow):
        """Visszaadja a szimulációhoz szükséges fizikai paramétereket."""
        base = MaterialManager.MATERIALS.get(mat_type, MaterialManager.MATERIALS["wood"])
        
        thickness = base.get("thickness", 0.1)
        area, inertia = MaterialManager.get_geometry(thickness, is_hollow)
        
        return {
            "E": base["E"],
            "density": base["density"], 
            "strength": base["strength"],
            "alpha": base["alpha"],
            "thickness": thickness,
            "area": area,
            "inertia": inertia
        }