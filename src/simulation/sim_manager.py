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
        self.broken_hashes = set() # Tracks IDs of broken constraints
        self.creak_timers = {} # {constraint_id: [time_accumulator, last_stress]}
        
        # Initialize Creak Timers with random offsets so they don't all creak at once
        for c in self.solver.constraints:
            # [time_since_last_check, stress_at_last_check]
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
            
            # --- AUDIO UPDATES ---
            self.check_break_sounds()
            self.check_creak_sounds(dt)

    def check_break_sounds(self):
        for c in self.solver.constraints:
            if c.broken and c not in self.broken_hashes:
                # It just broke!
                self.broken_hashes.add(c)
                
                if c.beam_ref.type == BeamType.VINE:
                    self.audio.play_sfx("vine_break")
                else:
                    self.audio.play_sfx("wood_break")

    def check_creak_sounds(self, dt):
        """
        Creaking Logic: 
        If material changes compression by at least 1% per 5s.
        """
        for c, data in self.creak_timers.items():
            if c.broken: continue
            
            # Update timer
            data[0] += dt
            
            # Check every 5 seconds
            if data[0] >= 5.0:
                current_stress = c.stress
                last_stress = data[1]
                
                # Difference > 1% (0.01)
                if abs(current_stress - last_stress) > 0.01:
                    # Only play if there is actually some load (stress > 5%)
                    # to avoid creaking when bridge is just settling at 0.001 stress
                    if current_stress > 0.05:
                        self.audio.play_sfx("creaking")
                
                # Reset
                data[0] = 0.0
                data[1] = current_stress

    def interpolate_color(self, color_start, color_end, t):
        r = color_start[0] + (color_end[0] - color_start[0]) * t
        g = color_start[1] + (color_end[1] - color_start[1]) * t
        b = color_start[2] + (color_end[2] - color_start[2]) * t
        return (int(r), int(g), int(b))

    def draw(self, surface, grid):
        # 1. Draw Beams
        for c in self.solver.constraints:
            if c.broken: continue

            start = grid.world_to_screen(c.p_a.x, c.p_a.y)
            end = grid.world_to_screen(c.p_b.x, c.p_b.y)
            
            base_color = c.beam_ref.color
            final_color = self.interpolate_color(base_color, (255, 0, 0), c.stress)
            
            width = 4 + int(c.stress * 4) 
            pygame.draw.line(surface, final_color, start, end, width)

            if c.beam_ref.hollow:
                pygame.draw.line(surface, (255, 255, 255), start, end, 2)

        # 2. Draw Nodes
        for p in self.solver.particles:
            pos = grid.world_to_screen(p.x, p.y)
            color = (200, 50, 50) if p.fixed else (255, 255, 255)
            pygame.draw.circle(surface, color, pos, 5)

        # 3. Draw Agent
        self.agent.draw(surface, grid)