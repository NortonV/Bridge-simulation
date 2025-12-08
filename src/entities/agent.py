import pygame
from core.constants import *
from core.material_manager import MaterialManager

class Ixchel:
    def __init__(self, audio_manager=None):
        self.active = False 
        self.x = 0
        self.y = 0
        self.velocity_x = 0
        self.mass = 5.0 
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
        
        # --- UPDATED: Fetch Speed Live ---
        speed = MaterialManager.AGENT["speed"]
        # ---------------------------------
        
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

    def update_static(self, dt, beams):
        if not self.active: return None
        
        self.handle_audio() 
        
        # --- UPDATED: Fetch Mass Live ---
        self.mass = MaterialManager.AGENT["mass"]
        # --------------------------------

        self.x += self.velocity_x * dt
        best_beam_y = -9999
        found_beam = None
        t_val = 0.0

        for beam in beams:
            if beam.type != "wood": continue 
            x1, y1 = beam.node_a.x, beam.node_a.y
            x2, y2 = beam.node_b.x, beam.node_b.y
            min_x, max_x = min(x1, x2), max(x1, x2)
            
            if min_x <= self.x <= max_x:
                if max_x - min_x < 0.01: continue 
                if x2 > x1:
                    t = (self.x - x1) / (x2 - x1)
                    beam_y = y1 + t * (y2 - y1)
                else:
                    t = (self.x - x2) / (x1 - x2)
                    beam_y = y2 + t * (y1 - y2)
                
                if beam_y > best_beam_y:
                    best_beam_y = beam_y
                    found_beam = beam
                    t_val = t

        if found_beam:
            self.y = best_beam_y
            return {
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