import pygame
import sys
from core.constants import *
from core.grid import Grid
from entities.bridge import Bridge
from entities.agent import Ixchel
from ui.editor import Editor
from ui.toolbar import Toolbar
from solvers.static_solver import StaticSolver
from core.serializer import Serializer
from ui.graph_overlay import GraphOverlay
from ui.property_menu import PropertyMenu 
from core.material_manager import MaterialManager
from audio.audio_manager import AudioManager

class BridgeBuilderApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ixchel's Bridge - Material Lab")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        w, h = self.screen.get_size()
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.large_font = pygame.font.SysFont("arial", 30, bold=True)
        
        self.grid = Grid(w, h)
        self.bridge = Bridge()
        self.toolbar = Toolbar(w, h)
        self.graph = GraphOverlay(20, h - 250, 400, 150)
        self.prop_menu = PropertyMenu(w, h)
        
        self.mode = "BUILD"
        self.static_solver = None
        self.broken_beams = set()
        
        self.error_message = None
        self.status_message = None
        self.message_timer = 0
        
        # --- UPDATED DEFAULT SCENE ---
        # Only 2 red nodes.
        # Moved 1 big square (5m) up and out from previous.
        self.bridge.add_node(-15, 10, fixed=True)
        self.bridge.add_node(15, 10, fixed=True)
        # The center floor node (0, -2) is intentionally removed.

        self.audio = AudioManager()
        self.audio.load_music("theme.mp3")
        self.audio.play_music()
        self.audio.load_sfx("wood_place", "wood_place.mp3")
        self.audio.load_sfx("vine_place", "vine_place.mp3")
        self.audio.load_sfx("step", "step.mp3") 

        self.vol_timer = 0
        self.vol_display_val = 0.5
        
        self.editor = Editor(self.grid, self.bridge, self.toolbar, self.audio)
        self.ghost_agent = Ixchel(self.audio) 

    def show_status(self, text):
        self.status_message = text
        self.error_message = None
        self.message_timer = 180

    def show_error(self, text):
        self.error_message = text
        self.status_message = None
        self.message_timer = 180

    def handle_input(self):
        mx, my = pygame.mouse.get_pos()
        world_pos = self.grid.snap(mx, my)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.audio.change_volume(0.01)
            self.vol_display_val = self.audio.volume
            self.vol_timer = 120
        if keys[pygame.K_DOWN]:
            self.audio.change_volume(-0.01)
            self.vol_display_val = self.audio.volume
            self.vol_timer = 120

        # --- Continuous Editor Input (Hold to Delete) ---
        if self.mode == "BUILD":
            self.editor.handle_continuous_input(world_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.quit()
            if self.prop_menu.handle_input(event):
                if self.prop_menu.should_quit:
                    self.quit()
                continue 
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                     self.prop_menu.toggle()
                
                if event.key == pygame.K_m: self.prop_menu.toggle()
                
                if event.key == pygame.K_TAB:
                    MaterialManager.PLACEMENT_MODE_HOLLOW = not MaterialManager.PLACEMENT_MODE_HOLLOW
                    mode_str = "HOLLOW" if MaterialManager.PLACEMENT_MODE_HOLLOW else "SOLID"
                    self.show_status(f"Mode: {mode_str}")

                if event.key == pygame.K_g: self.graph.toggle()

                is_ctrl = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])
                if is_ctrl and event.key == pygame.K_s:
                    if self.mode == "BUILD":
                        success, msg = Serializer.save_as(self.bridge)
                        if success: self.show_status(msg)
                        else: self.show_error(msg)
                if is_ctrl and event.key == pygame.K_l:
                    if self.mode == "BUILD":
                        success, msg = Serializer.open_file(self.bridge)
                        if success: self.show_status(msg)
                        else: self.show_error(msg)
                        self.graph.reset_data()
                
                # --- SPACE to Analyze ---
                if event.key == pygame.K_SPACE:
                    if self.mode == "BUILD": 
                        self.run_static_analysis()
                    elif self.mode == "ANALYSIS": 
                        self.stop_analysis()
                    continue # Prevents falling through to other checks

                # --- Analysis Mode Controls (Cancel) ---
                if self.mode == "ANALYSIS":
                    # We check for SPACE above, so here we check other cancellation keys
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_x]:
                        self.stop_analysis()
                        continue

            if event.type == pygame.MOUSEWHEEL:
                if event.y != 0:
                    change = event.y * 0.05
                    self.audio.change_volume(change)
                    self.vol_display_val = self.audio.volume
                    self.vol_timer = 120 

            self.toolbar.handle_input(event)
            
            if self.mode == "BUILD":
                self.editor.handle_input(event, world_pos)
        
        if self.mode == "ANALYSIS":
            self.ghost_agent.handle_input()

    def run_static_analysis(self):
        self.ghost_agent.mass = MaterialManager.AGENT["mass"]
        solver = StaticSolver(self.bridge)
        if not solver.is_stable():
            self.show_error(solver.error_msg)
            return
        success = solver.solve(point_load=None)
        if not success:
            self.show_error(solver.error_msg)
        else:
            self.static_solver = solver
            self.mode = "ANALYSIS"
            self.show_status(f"Analysis (Mass: {self.ghost_agent.mass:.1f})")
            self.graph.reset_data()
            self.broken_beams.clear()
            
            start_node = None
            min_x = 9999
            for beam in self.bridge.beams:
                if beam.type == "wood":
                    if beam.node_a.x < min_x:
                        min_x = beam.node_a.x
                        start_node = beam.node_a
                    if beam.node_b.x < min_x:
                        min_x = beam.node_b.x
                        start_node = beam.node_b
            if start_node:
                self.ghost_agent.spawn(start_node.x, start_node.y + 1.0)
            else:
                self.ghost_agent.active = False

    def stop_analysis(self):
        self.mode = "BUILD"
        self.static_solver = None
        self.toolbar.active_index = 0
        self.show_status("Build Mode")
        self.error_message = None
        self.broken_beams.clear()
        self.audio.stop_sfx("step") 

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.error_message = None
                self.status_message = None
        
        self.prop_menu.update()

        max_val = 0.0
        max_perc = 0.0
        
        if self.mode == "ANALYSIS" and self.static_solver:
            self.ghost_agent.mass = MaterialManager.AGENT["mass"]
            load_info = self.ghost_agent.update_static(1.0/60.0, self.bridge.beams)
            self.static_solver.solve(point_load=load_info)
            
            for beam, force in self.static_solver.results.items():
                if abs(force) > max_val: max_val = abs(force)
                
                props = MaterialManager.get_properties(beam.type, beam.hollow)
                capacity = props["E"] * props["strength"] # Approximate Capacity
                ratio = abs(force) / capacity
                
                pct = ratio * 100.0
                if pct > max_perc: max_perc = pct
                    
                if ratio >= 1.0:
                    self.broken_beams.add(beam)
            
            self.graph.update(max_val, max_perc, "ANALYSIS")
        else:
            self.graph.update(0, 0, "BUILD")

        if self.vol_timer > 0: self.vol_timer -= 1

    def draw(self):
        self.grid.draw(self.screen)
        
        if self.mode == "BUILD":
            self.editor.draw(self.screen)
            self.draw_hud()
            
        elif self.mode == "ANALYSIS":
            self.draw_analysis_results()
            self.ghost_agent.draw(self.screen, self.grid)

        self.toolbar.draw(self.screen)
        self.graph.draw(self.screen)
        self.prop_menu.draw(self.screen)
        
        msg_text = None
        msg_color = (255, 255, 255)
        if self.error_message:
            msg_text = self.error_message
            msg_color = (255, 50, 50)
        elif self.status_message:
            msg_text = self.status_message
            msg_color = (50, 255, 50)
            
        if msg_text:
            text = self.large_font.render(msg_text, True, msg_color)
            bg = pygame.Surface((text.get_width()+20, text.get_height()+10))
            bg.fill((30,30,30))
            rect = text.get_rect(center=(self.screen.get_width()//2, 100))
            bg_rect = bg.get_rect(center=(self.screen.get_width()//2, 100))
            self.screen.blit(bg, bg_rect)
            self.screen.blit(text, rect)
        
        if self.mode == "BUILD":
            help_txt = self.font.render("Space: Analyze | Tab: Hollow/Solid | X: Delete", True, (50,50,50))
            self.screen.blit(help_txt, (self.screen.get_width() - 650, 20))
        
        self.draw_volume_popup()

        pygame.display.flip()

    def draw_analysis_results(self):
         if not self.static_solver: return
         
         view_mode = self.prop_menu.view_mode 
         text_mode = self.prop_menu.text_mode
         
         for node in self.bridge.nodes:
            pos = self.grid.world_to_screen(node.x, node.y)
            color = (200, 50, 50) if node.fixed else (100, 100, 100)
            pygame.draw.circle(self.screen, color, pos, 6)
         
         for beam, force in self.static_solver.results.items():
            start = self.grid.world_to_screen(beam.node_a.x, beam.node_a.y)
            end = self.grid.world_to_screen(beam.node_b.x, beam.node_b.y)
            
            color = (100, 100, 100)
            
            props = MaterialManager.get_properties(beam.type, beam.hollow)
            thickness = props['thickness']
            
            # --- Visual Thickness ---
            # Map thickness (m) to pixels. 0.1m * 40ppm = 4px
            width = max(1, int(thickness * PPM))
            
            capacity = props["E"] * props["strength"]
            ratio = abs(force) / capacity
            
            if view_mode == 0: 
                if force < 0: color = (50, 50, 255) 
                else:         color = (255, 50, 50) 
            
            elif view_mode == 1: 
                color = beam.color
                
            elif view_mode == 2: 
                if beam in self.broken_beams:
                    color = (0, 0, 0)
                else:
                    base_c = beam.color
                    target_c = (255, 0, 0)
                    t = min(1.0, ratio) 
                    r = int(base_c[0] + (target_c[0] - base_c[0]) * t)
                    g = int(base_c[1] + (target_c[1] - base_c[1]) * t)
                    b = int(base_c[2] + (target_c[2] - base_c[2]) * t)
                    color = (r, g, b)

            pygame.draw.line(self.screen, color, start, end, width)
            
            if beam.hollow:
                 # Ensure hollow line is thinner than the main line
                 inner_w = max(1, width - 4)
                 pygame.draw.line(self.screen, (255,255,255), start, end, inner_w)

            if text_mode != 2: 
                mx = (start[0] + end[0]) // 2
                my = (start[1] + end[1]) // 2
                
                label = ""
                if text_mode == 0: label = f"{int(abs(force))}N"
                elif text_mode == 1: label = f"{int(ratio * 100)}%"
                    
                text = self.font.render(label, True, (255, 255, 255))
                bg_rect = text.get_rect(center=(mx, my))
                bg_rect.inflate_ip(10, 6)
                pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
                pygame.draw.rect(self.screen, color, bg_rect, 2) 
                self.screen.blit(text, text.get_rect(center=(mx, my)))

    def draw_volume_popup(self):
            if self.vol_timer <= 0: return

            w, h = self.screen.get_size()
            box_w, box_h = 220, 60
            margin = 30
            x = w - box_w - margin
            y = h - box_h - margin
            
            alpha = 230
            if self.vol_timer < 20: 
                alpha = int(230 * (self.vol_timer / 20))
                
            surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (30, 30, 40, alpha), (0, 0, box_w, box_h), border_radius=10)
            pygame.draw.rect(surf, (200, 200, 200, alpha), (0, 0, box_w, box_h), 2, border_radius=10)
            
            bar_max_w = 180
            bar_h = 6
            bar_x = (box_w - bar_max_w) // 2
            bar_y = 40
            pygame.draw.rect(surf, (60, 60, 70, alpha), (bar_x, bar_y, bar_max_w, bar_h), border_radius=3)
            
            current_w = int(bar_max_w * self.vol_display_val)
            if current_w > 0:
                pygame.draw.rect(surf, (0, 200, 255, alpha), (bar_x, bar_y, current_w, bar_h), border_radius=3)

            txt_str = f"Volume: {int(self.vol_display_val * 100)}%"
            text = self.font.render(txt_str, True, (255, 255, 255))
            text.set_alpha(alpha)
            text_rect = text.get_rect(center=(box_w // 2, 20))
            surf.blit(text, text_rect)
            
            self.screen.blit(surf, (x, y))

    def draw_hud(self):
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.grid.snap(mx, my)
        sx, sy = self.grid.world_to_screen(wx, wy)
        pygame.draw.circle(self.screen, COLOR_CURSOR, (sx, sy), 8, 2)
        info = f"Nodes: {len(self.bridge.nodes)} | Beams: {len(self.bridge.beams)}"
        text = self.font.render(info, True, COLOR_TEXT)
        self.screen.blit(text, (20, 20))

    def quit(self):
        pygame.quit()
        sys.exit()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    app = BridgeBuilderApp()
    app.run()