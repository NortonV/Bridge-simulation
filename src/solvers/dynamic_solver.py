import math
from core.constants import *
from core.material_manager import MaterialManager

class PhysicsParticle:
    def __init__(self, node=None, x=0, y=0, fixed=False):
        if node:
            self.id = id(node)
            self.x = node.x
            self.y = node.y
            self.fixed = node.fixed
        else:
            self.id = id(self)
            self.x = x
            self.y = y
            self.fixed = fixed
        
        self.old_x = self.x
        self.old_y = self.y
        
        self.mass = 0.1       
        self.inv_mass = 1.0   

class PhysicsConstraint:
    def __init__(self, beam, particle_a, particle_b, can_break=True):
        self.beam_ref = beam
        self.p_a = particle_a
        self.p_b = particle_b
        self.rest_length = beam.length
        self.broken = False
        self.stress = 0.0
        self.can_break = can_break # NEW: Breakage Limit Flag
        
        # Simulation Properties
        self.stiffness = 1.0
        self.breaking_threshold = 0.1
        self.density = 1.0
        
        self.update_props()

    def update_props(self):
        props = MaterialManager.get_properties(self.beam_ref.type, self.beam_ref.hollow)
        self.density = props["density"]
        self.breaking_threshold = props["strength"]
        self.stiffness = props["E"] / 4000.0 

class DynamicSolver:
    def __init__(self, bridge_data):
        self.gravity = 9.81
        self.global_damping = 0.999 
        
        self.particles = []
        self.constraints = []
        self.time_elapsed = 0.0
        
        # 1. Create Particles
        node_map = {}
        for node in bridge_data.nodes:
            p = PhysicsParticle(node=node)
            self.particles.append(p)
            node_map[node] = p
            
        # 2. Create Constraints
        for beam in bridge_data.beams:
            p_a = node_map[beam.node_a]
            p_b = node_map[beam.node_b]
            # Initial beams can break
            c = PhysicsConstraint(beam, p_a, p_b, can_break=True)
            self.constraints.append(c)
            
        # 3. Mass Calc
        self.update_live_properties()
        
        # 4. PRE-SOLVE
        for _ in range(15):
            self.solve_constraints()
            
        # 5. Reset history
        for p in self.particles:
            p.old_x = p.x
            p.old_y = p.y

    def update_live_properties(self):
        BASE_JOINT_MASS = 0.1 
        
        for p in self.particles:
            if p.fixed:
                p.mass = 0.0
                p.inv_mass = 0.0
            else:
                p.mass = BASE_JOINT_MASS

        for c in self.constraints:
            if c.broken: continue
            
            c.update_props()
            beam_mass = c.rest_length * c.density
            
            if not c.p_a.fixed: c.p_a.mass += beam_mass * 0.5
            if not c.p_b.fixed: c.p_b.mass += beam_mass * 0.5

        for p in self.particles:
            if not p.fixed:
                if p.mass < 0.001: p.mass = 0.001 
                p.inv_mass = 1.0 / p.mass

    def update(self, dt):
        self.time_elapsed += dt
        SUB_STEPS = 12
        sub_dt = dt / SUB_STEPS
        
        for _ in range(SUB_STEPS):
            self.integrate_verlet(sub_dt)
            self.solve_constraints()
            self.solve_floor_constraint()
            
        self.calculate_stress_and_breakage()
        self.constraints = [c for c in self.constraints if not c.broken]

    def integrate_verlet(self, dt):
        for p in self.particles:
            if p.fixed: continue
            
            vx = (p.x - p.old_x) * self.global_damping
            vy = (p.y - p.old_y) * self.global_damping
            
            # Aerodynamic Drag
            speed_sq = vx*vx + vy*vy
            if speed_sq > 0.1:
                drag = 1.0 / (1.0 + speed_sq * 0.005)
                vx *= drag
                vy *= drag
            
            MAX_V = 100.0 
            vx = max(-MAX_V, min(MAX_V, vx))
            vy = max(-MAX_V, min(MAX_V, vy))
            
            p.old_x = p.x
            p.old_y = p.y
            
            grav_y = -self.gravity * dt * dt 
            
            p.x += vx
            p.y += vy + grav_y

    def solve_constraints(self):
        for c in self.constraints:
            if c.broken: continue

            dx = c.p_b.x - c.p_a.x
            dy = c.p_b.y - c.p_a.y
            
            try:
                dist = math.sqrt(dx**2 + dy**2)
            except OverflowError:
                c.broken = True
                continue

            if dist < 0.0001: continue
            
            if c.beam_ref.type == "vine" and dist < c.rest_length:
                continue
                
            deformation = dist - c.rest_length
            correction = deformation * c.stiffness
            
            w_a = c.p_a.inv_mass
            w_b = c.p_b.inv_mass
            w_total = w_a + w_b
            
            if w_total == 0: continue
            
            move_a = +(w_a / w_total) * correction
            move_b = -(w_b / w_total) * correction
            
            nx = dx / dist
            ny = dy / dist
            
            if not c.p_a.fixed:
                c.p_a.x += nx * move_a
                c.p_a.y += ny * move_a
                
            if not c.p_b.fixed:
                c.p_b.x += nx * move_b
                c.p_b.y += ny * move_b

    def calculate_stress_and_breakage(self):
        if self.time_elapsed < 0.3: return

        new_constraints = []
        new_particles = []

        for c in self.constraints:
            if c.broken: continue
            
            dx = c.p_b.x - c.p_a.x
            dy = c.p_b.y - c.p_a.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist == 0: continue

            if c.beam_ref.type == "vine" and dist < c.rest_length:
                c.stress = 0.0
                continue

            strain = (dist - c.rest_length) / c.rest_length
            c.stress = min(1.0, abs(strain) / c.breaking_threshold)
            
            # --- "BREAK ONCE" LOGIC ---
            if not c.can_break:
                continue
            
            if abs(strain) > c.breaking_threshold:
                c.broken = True
                
                # Note: "Length < 0.5" check removed as it is now redundant.
                
                # Dampen Parents
                DAMP_SHOCK = 0.5
                va_x = c.p_a.x - c.p_a.old_x
                va_y = c.p_a.y - c.p_a.old_y
                vb_x = c.p_b.x - c.p_b.old_x
                vb_y = c.p_b.y - c.p_b.old_y
                
                c.p_a.old_x = c.p_a.x - (va_x * DAMP_SHOCK)
                c.p_a.old_y = c.p_a.y - (va_y * DAMP_SHOCK)
                c.p_b.old_x = c.p_b.x - (vb_x * DAMP_SHOCK)
                c.p_b.old_y = c.p_b.y - (vb_y * DAMP_SHOCK)

                # Create Broken Pieces
                mid_x = (c.p_a.x + c.p_b.x) / 2
                mid_y = (c.p_a.y + c.p_b.y) / 2
                
                p_mid_a = PhysicsParticle(x=mid_x, y=mid_y, fixed=False)
                p_mid_b = PhysicsParticle(x=mid_x, y=mid_y, fixed=False)
                
                vx_avg = (va_x + vb_x) / 2
                vy_avg = (va_y + vb_y) / 2
                
                DAMP_NEW = 0.2
                p_mid_a.old_x = p_mid_a.x - (vx_avg * DAMP_NEW)
                p_mid_a.old_y = p_mid_a.y - (vy_avg * DAMP_NEW)
                
                p_mid_b.old_x = p_mid_b.x - (vx_avg * DAMP_NEW)
                p_mid_b.old_y = p_mid_b.y - (vy_avg * DAMP_NEW)
                
                new_particles.extend([p_mid_a, p_mid_b])
                
                # Create NEW broken constraints with can_break=False
                c1 = PhysicsConstraint(c.beam_ref, c.p_a, p_mid_a, can_break=False)
                c1.rest_length = c.rest_length / 2.0
                c1.broken = False
                
                c2 = PhysicsConstraint(c.beam_ref, c.p_b, p_mid_b, can_break=False)
                c2.rest_length = c.rest_length / 2.0
                c2.broken = False

                new_constraints.extend([c1, c2])

        self.particles.extend(new_particles)
        self.constraints.extend(new_constraints)

    def solve_floor_constraint(self):
        FLOOR_Y = -14.0
        for p in self.particles:
            if p.fixed: continue
            
            if p.y < FLOOR_Y:
                p.y = FLOOR_Y
                friction = 0.5
                vx = (p.x - p.old_x) * friction
                p.old_x = p.x - vx