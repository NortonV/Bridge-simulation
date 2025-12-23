import math
from core.constants import *

class BeamType:
    WOOD = "wood"
    BAMBOO = "bamboo"
    VINE = "vine"
    STEEL = "steel"
    CABLE = "cable"
    SPAGHETTI = "spaghetti"

class Beam:
    def __init__(self, node_a, node_b, material_type=BeamType.WOOD):
        self.node_a = node_a
        self.node_b = node_b
        self.type = material_type
        self.stress = 0.0
        # Added hollow_ratio property
        self.hollow_ratio = 0.0

    @property
    def color(self):
        if self.type == BeamType.VINE: return COLOR_VINE
        if self.type == BeamType.BAMBOO: return COLOR_BAMBOO
        if self.type == BeamType.STEEL: return COLOR_STEEL
        if self.type == BeamType.CABLE: return COLOR_CABLE
        if self.type == BeamType.SPAGHETTI: return COLOR_SPAGHETTI
        return COLOR_WOOD

    @property
    def length(self):
        dx = self.node_b.x - self.node_a.x
        dy = self.node_b.y - self.node_a.y
        return math.sqrt(dx**2 + dy**2)