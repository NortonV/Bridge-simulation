import math
from core.constants import *
from core.material_manager import MaterialManager

class BeamType:
    WOOD = "wood"
    BAMBOO = "bamboo"
    STEEL = "steel"
    SPAGHETTI = "spaghetti"

class Beam:
    def __init__(self, node_a, node_b, material_type=BeamType.WOOD):
        self.node_a = node_a
        self.node_b = node_b
        self.type = material_type
        self.stress = 0.0

    @property
    def hollow_ratio(self):
        """Dynamically get hollow_ratio from material settings."""
        return MaterialManager.MATERIALS.get(self.type, {}).get("hollow_ratio", 0.0)

    @property
    def color(self):
        if self.type == BeamType.BAMBOO: return COLOR_BAMBOO
        if self.type == BeamType.STEEL: return COLOR_STEEL
        if self.type == BeamType.SPAGHETTI: return COLOR_SPAGHETTI
        return COLOR_WOOD

    @property
    def length(self):
        dx = self.node_b.x - self.node_a.x
        dy = self.node_b.y - self.node_a.y
        return math.sqrt(dx**2 + dy**2)