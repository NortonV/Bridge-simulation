import pygame
import math
from core.constants import *
from core.material_manager import MaterialManager

class Ixchel:
    def __init__(self, audio_manager=None):
        self.active = False 
        self.x = 0
        self.y = 0
        self.velocity_x = 0
        self.on_ground = False
        
        # Audio
        self.audio = audio_manager
        self.was_moving = False 

    def spawn(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.velocity_x = 0
        self.was_moving = False

    def handle_input(self):
        if not self.active: return
        
        keys = pygame.key.get_pressed()
        
        # Fetch Speed Live
        speed = MaterialManager.AGENT["speed"]
        
        self.velocity_x = 0
        if keys[pygame.K_LEFT]:
            self.velocity_x = -speed
        if keys[pygame.K_RIGHT]:
            self.velocity_x = speed
        
        if keys[pygame.K_r]:
            self.y += 2.0 
            self.velocity_x = 0

    def handle_audio(self):
        if not self.audio: return
        is_moving = abs(self.velocity_x) > 0.1
        
        if is_moving and not self.was_moving:
            self.audio.play_sfx("step", loop=True)
        elif not is_moving and self.was_moving:
            self.audio.stop_sfx("step")
            
        self.was_moving = is_moving

    def update_static(self, dt, beams, displacements=None, exaggeration=1.0):
        if not self.active: return None
        
        self.handle_audio() 
        
        # Fetch Mass Live
        self.mass = MaterialManager.AGENT["mass"]

        self.x += self.velocity_x * dt
        best_beam_y = -9999
        found_beam = None
        t_val = 0.0

        for beam in beams:
            if beam.type != "wood": continue 
            
            # --- CALCULATE DEFORMED GEOMETRY ---
            node_a = beam.node_a
            node_b = beam.node_b
            
            # Get original coordinates
            x1_orig, y1_orig = node_a.x, node_a.y
            x2_orig, y2_orig = node_b.x, node_b.y
            
            # Apply displacements if they exist
            da_x, da_y, da_theta = 0, 0, 0
            db_x, db_y, db_theta = 0, 0, 0
            
            if displacements:
                da_x, da_y, da_theta = displacements.get(node_a, (0,0,0))
                db_x, db_y, db_theta = displacements.get(node_b, (0,0,0))

            # Calculate Visual Endpoints (Exaggerated)
            p1_x = x1_orig + da_x * exaggeration
            p1_y = y1_orig + da_y * exaggeration
            p2_x = x2_orig + db_x * exaggeration
            p2_y = y2_orig + db_y * exaggeration

            # Check X bounds based on DEFORMED positions
            min_x, max_x = min(p1_x, p2_x), max(p1_x, p2_x)
            
            if min_x <= self.x <= max_x:
                if max_x - min_x < 0.01: continue 
                

                beam_dx = p2_x - p1_x
                beam_dy = p2_y - p1_y
                beam_len_sq = beam_dx*beam_dx + beam_dy*beam_dy
                
                # Vector from Node A to Agent
                agent_dx = self.x - p1_x
                agent_dy = self.y - p1_y

                if beam_len_sq > 0.00001:
                    # Dot Product Projection: (AgentVector . BeamVector) / |BeamVector|^2
                    dot = agent_dx * beam_dx + agent_dy * beam_dy
                    t = dot / beam_len_sq
                else:
                    t = 0.5 # Fallback for zero-length beams
                
                # --- CUBIC HERMITE SPLINE INTERPOLATION (Matches Renderer) ---
                if displacements:
                    chord_dx = p2_x - p1_x
                    chord_dy = p2_y - p1_y
                    L_deformed = math.hypot(chord_dx, chord_dy)
                    psi = math.atan2(chord_dy, chord_dx)
                    
                    orig_dx = x2_orig - x1_orig
                    orig_dy = y2_orig - y1_orig
                    alpha = math.atan2(orig_dy, orig_dx)
                    
                    # Rotations relative to the new chord
                    rot1 = (alpha + da_theta * exaggeration) - psi
                    rot2 = (alpha + db_theta * exaggeration) - psi
                    
                    # --- ADD THE SAME FIX HERE ---
                    while rot1 > math.pi: rot1 -= 2 * math.pi
                    while rot1 < -math.pi: rot1 += 2 * math.pi
                    while rot2 > math.pi: rot2 -= 2 * math.pi
                    while rot2 < -math.pi: rot2 += 2 * math.pi
                    
                    # Shape functions
                    s = t
                    h1 = s**3 - 2*s**2 + s
                    h2 = s**3 - s**2
                    
                    v = L_deformed * (h1 * rot1 + h2 * rot2) # Perpendicular deflection
                    u = s * L_deformed                       # Axial distance along chord
                    
                    cp = math.cos(psi)
                    sp = math.sin(psi)
                    
                    # Final calculated Y on the curve
                    beam_y = p1_y + u*sp + v*cp
                else:
                    # Fallback to linear interpolation if no simulation data
                    beam_y = p1_y + t * (p2_y - p1_y)
                
                if beam_y > best_beam_y:
                    best_beam_y = beam_y
                    found_beam = beam
                    t_val = t

        if found_beam:
            self.y = best_beam_y
            return {
                'beam': found_beam,
                'node_a': found_beam.node_a if found_beam.node_a.x < found_beam.node_b.x else found_beam.node_b,
                'node_b': found_beam.node_b if found_beam.node_a.x < found_beam.node_b.x else found_beam.node_a,
                't': t_val,
                'mass': self.mass
            }
        else:
            if self.y > -10: self.y -= 9.81 * dt
            return None

    def draw(self, surface, grid):
        if not self.active: return
        screen_x, screen_y = grid.world_to_screen(self.x, self.y)
        pygame.draw.circle(surface, (0, 255, 255), (screen_x, screen_y - 20), 10) 
        pygame.draw.line(surface, (0, 255, 255), (screen_x, screen_y - 20), (screen_x, screen_y), 4)