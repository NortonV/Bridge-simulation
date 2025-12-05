import math
from core.constants import *
from core.material_manager import MaterialManager

class PhysicsParticle:
    def __init__(self, node):
        self.id = id(node)
        self.x = node.x
        self.y = node.y
        self.old_x = node.x
        self.old_y = node.y
        self.fixed = node.fixed
        self.mass = 0.5 

class PhysicsConstraint:
    def __init__(self, beam, particle_a, particle_b):
        self.beam_ref = beam
        self.p_a = particle_a
        self.p_b = particle_b
        self.rest_length = beam.length
        self.broken = False
        self.stress = 0.0
        
        # Initial load
        self.update_props()

    def update_props(self):
        """Fetches the latest properties from the Manager."""
        props = MaterialManager.get_properties(self.beam_ref.type, self.beam_ref.hollow)
        
        # Update Physics Constants
        self.stiffness = props["E"] / 2000.0  
        self.breaking_threshold = props["strength"]
        self.density = props["density"]

class DynamicSolver:
    def __init__(self, bridge_data):
        self.gravity = 9.81
        self.friction = 0.97 
        self.particles = []
        self.constraints = []
        
        # 1. Create Particles
        node_map = {}
        for node in bridge_data.nodes:
            p = PhysicsParticle(node)
            self.particles.append(p)
            node_map[node] = p
            
        # 2. Create Constraints
        for beam in bridge_data.beams:
            p_a = node_map[beam.node_a]
            p_b = node_map[beam.node_b]
            c = PhysicsConstraint(beam, p_a, p_b)
            self.constraints.append(c)
            
        # 3. Calculate initial Mass
        self.update_live_properties()

    def update_live_properties(self):
        """
        Re-reads all material sliders and updates mass/stiffness live.
        This must be called every frame if we want live tweaking.
        """
        # A. Reset Particle Mass to base (joint weight)
        for p in self.particles:
            p.mass = 0.5

        # B. Update Constraints & Redistribute Mass
        for c in self.constraints:
            if c.broken: continue
            
            # 1. Update Stiffness/Strength
            c.update_props()
            
            # 2. Re-calculate Mass based on new Density
            beam_mass = c.rest_length * c.density
            c.p_a.mass += beam_mass * 0.5
            c.p_b.mass += beam_mass * 0.5

    def update(self, dt):
        sub_steps = 8
        sub_dt = dt / sub_steps
        
        for _ in range(sub_steps):
            self.apply_gravity()
            self.apply_verlet()
            self.solve_constraints()
            self.constrain_points()
            
        self.constraints = [c for c in self.constraints if not c.broken]

    def apply_gravity(self):
        for p in self.particles:
            if not p.fixed:
                p.y -= self.gravity * 0.0005

    def apply_verlet(self):
        for p in self.particles:
            if not p.fixed:
                vx = (p.x - p.old_x) * self.friction
                vy = (p.y - p.old_y) * self.friction
                p.old_x = p.x
                p.old_y = p.y
                p.x += vx
                p.y += vy

    def solve_constraints(self):
        for c in self.constraints:
            if c.broken: continue

            dx = c.p_b.x - c.p_a.x
            dy = c.p_b.y - c.p_a.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist == 0: continue
            
            if c.beam_ref.type == "vine" and dist < c.rest_length:
                c.stress = 0.0
                continue
            
            deformation = dist - c.rest_length
            strain = deformation / c.rest_length
            
            if strain > 0:
                c.stress = min(1.0, strain / c.breaking_threshold)
            else:
                c.stress = 0.0
                
            if strain > c.breaking_threshold:
                c.broken = True
                continue

            diff = (dist - c.rest_length) / dist
            
            total_mass = c.p_a.mass + c.p_b.mass
            ratio_a = c.p_b.mass / total_mass 
            ratio_b = c.p_a.mass / total_mass
            
            offset_x = dx * diff * c.stiffness
            offset_y = dy * diff * c.stiffness
            
            if not c.p_a.fixed:
                c.p_a.x += offset_x * ratio_a
                c.p_a.y += offset_y * ratio_a
            if not c.p_b.fixed:
                c.p_b.x -= offset_x * ratio_b
                c.p_b.y -= offset_y * ratio_b

    def constrain_points(self):
        for p in self.particles:
            if p.y < -15: p.y = -15