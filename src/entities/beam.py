import math
from core.constants import *

class BeamType:
    WOOD = "wood"
    BAMBOO = "bamboo"
    VINE = "vine"

class Beam:
    def __init__(self, node_a, node_b, material_type=BeamType.WOOD):
        self.node_a = node_a
        self.node_b = node_b
        self.type = material_type
        
        # Engineering Properties
        self.hollow = False      # Solid by default
        self.thickness = 0.1     # 10cm diameter
        self.stress = 0.0        # Current load (0.0 - 1.0)

    @property
    def color(self):
        """Returns the color based on material type."""
        if self.type == BeamType.VINE: return COLOR_VINE
        if self.type == BeamType.BAMBOO: return COLOR_BAMBOO
        return COLOR_WOOD

    @property
    def length(self):
        """Calculates real-world length in meters."""
        dx = self.node_b.x - self.node_a.x
        dy = self.node_b.y - self.node_a.y
        return math.sqrt(dx**2 + dy**2)