import pygame
import random
from solvers.dynamic_solver import DynamicSolver
from entities.agent import Ixchel 
from entities.beam import BeamType

class SimulationManager:
    def __init__(self, bridge_data, audio_manager):
        self.solver = DynamicSolver(bridge_data)
        self.audio = audio_manager
        
        # Pass audio to agent
        self.agent = Ixchel(audio_manager) 
        
        self.is_running = True
        
        # --- STATE TRACKING FOR AUDIO ---
        self.broken_hashes = set()
        self.creak_timers = {} 
        
        for c in self.solver.constraints:
            self.creak_timers[c] = [random.uniform(0, 5.0), 0.0]

        # --- SPAWN LOGIC ---
        start_node = None
        min_x = 9999
        for beam in bridge_data.beams:
            if beam.type == "wood":
                if beam.node_a.x < min_x:
                    min_x = beam.node_a.x
                    start_node = beam.node_a
                if beam.node_b.x < min_x:
                    min_x = beam.node_b.x
                    start_node = beam.node_b
        
        if start_node:
            self.agent.spawn(start_node.x, start_node.y + 1.0)
        else:
            print("No WOOD beams found! Ixchel will not spawn.")

    def update(self, dt):
        if self.is_running:
            self.solver.update(dt)
            self.agent.handle_input()
            self.agent.update(dt, self.solver.constraints)
            
            self.check_break_sounds()
            self.check_creak_sounds(dt)

    def check_break_sounds(self):
        for c in self.solver.constraints:
            if c.broken and c not in self.broken_hashes:
                self.broken_hashes.add(c)
                if c.beam_ref.type == BeamType.VINE:
                    self.audio.play_sfx("vine_break")
                else:
                    self.audio.play_sfx("wood_break")

    def check_creak_sounds(self, dt):
        for c, data in self.creak_timers.items():
            if c.broken: continue
            data[0] += dt
            if data[0] >= 5.0:
                current_stress = c.stress
                last_stress = data[1]
                if abs(current_stress - last_stress) > 0.01:
                    if current_stress > 0.05:
                        self.audio.play_sfx("creaking")
                data[0] = 0.0
                data[1] = current_stress

    def interpolate_color(self, color_start, color_end, t):
        # Safety clamp for t
        t = max(0.0, min(1.0, t))
        r = color_start[0] + (color_end[0] - color_start[0]) * t
        g = color_start[1] + (color_end[1] - color_start[1]) * t
        b = color_start[2] + (color_end[2] - color_start[2]) * t
        return (int(r), int(g), int(b))

    def clamp_screen_coords(self, point):
        """Prevents Pygame crash by clamping huge coordinates."""
        x, y = point
        # Pygame safe range (approx short int)
        MIN_COORD, MAX_COORD = -10000, 10000
        return (
            max(MIN_COORD, min(MAX_COORD, x)),
            max(MIN_COORD, min(MAX_COORD, y))
        )

    def draw(self, surface, grid):
        # 1. Draw Beams
        for c in self.solver.constraints:
            if c.broken: continue

            # Get coordinates
            raw_start = grid.world_to_screen(c.p_a.x, c.p_a.y)
            raw_end = grid.world_to_screen(c.p_b.x, c.p_b.y)
            
            # CRITICAL FIX: Clamp coordinates to prevent "invalid end_pos" crash
            start = self.clamp_screen_coords(raw_start)
            end = self.clamp_screen_coords(raw_end)
            
            base_color = c.beam_ref.color
            final_color = self.interpolate_color(base_color, (255, 0, 0), c.stress)
            
            width = 4 + int(c.stress * 4) 
            pygame.draw.line(surface, final_color, start, end, width)

            if c.beam_ref.hollow:
                pygame.draw.line(surface, (255, 255, 255), start, end, 2)

        # 2. Draw Nodes
        for p in self.solver.particles:
            raw_pos = grid.world_to_screen(p.x, p.y)
            pos = self.clamp_screen_coords(raw_pos)
            
            color = (200, 50, 50) if p.fixed else (255, 255, 255)
            pygame.draw.circle(surface, color, pos, 5)

        # 3. Draw Agent
        self.agent.draw(surface, grid)