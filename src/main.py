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
        pygame.display.set_caption("Ixchel Hídja - Mérnöki Laboratórium")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        w, h = self.screen.get_size()
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.large_font = pygame.font.SysFont("arial", 30, bold=True)
        
        self.grid = Grid(w, h)
        self.bridge = Bridge()
        self.toolbar = Toolbar(w, h)
        self.graph = GraphOverlay(20, h - 300, 300, 150) # Moved up slightly
        self.prop_menu = PropertyMenu(w, h)
        
        self.mode = "BUILD"
        self.static_solver = None
        self.broken_beams = set()
        
        self.error_message = None
        self.status_message = None
        self.message_timer = 0
        
        # Setup Default Scene
        self.bridge.add_node(-15, 10, fixed=True)
        self.bridge.add_node(15, 10, fixed=True)

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
                    mode_str = "ÜREGES (Cső)" if MaterialManager.PLACEMENT_MODE_HOLLOW else "TÖMÖR (Rúd)"
                    self.show_status(f"Mód: {mode_str}")

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
                
                if event.key == pygame.K_SPACE:
                    if self.mode == "BUILD": 
                        self.run_static_analysis()
                    elif self.mode == "ANALYSIS": 
                        self.stop_analysis()
                    continue

                if self.mode == "ANALYSIS":
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
            # Translate common error
            if "Mechanism" in solver.error_msg:
                self.show_error("Instabil szerkezet! (Mechanizmus)")
            else:
                self.show_error(solver.error_msg)
            return
        success = solver.solve(point_load=None)
        if not success:
            self.show_error("Instabil: Szinguláris Mátrix")
        else:
            self.static_solver = solver
            self.mode = "ANALYSIS"
            self.show_status(f"Szimuláció (Tömeg: {self.ghost_agent.mass:.1f}kg)")
            self.graph.reset_data()
            self.broken_beams.clear()
            self.graph.visible = True
            
            # Find spawn point
            start_node = None
            min_x = 9999
            for beam in self.bridge.beams:
                if beam.type == "wood":
                    if beam.node_a.x < min_x: min_x = beam.node_a.x; start_node = beam.node_a
                    if beam.node_b.x < min_x: min_x = beam.node_b.x; start_node = beam.node_b
            if start_node:
                self.ghost_agent.spawn(start_node.x, start_node.y + 1.0)
            else:
                self.ghost_agent.active = False

    def stop_analysis(self):
        self.mode = "BUILD"
        self.static_solver = None
        self.toolbar.active_index = 0
        self.show_status("Építés Mód")
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
                capacity = props["E"] * props["strength"]
                ratio = abs(force) / capacity
                pct = ratio * 100.0
                if pct > max_perc: max_perc = pct
                if ratio >= 1.0: self.broken_beams.add(beam)
            
            self.graph.update(max_val, max_perc, "ANALYSIS")
        else:
            self.graph.update(0, 0, "BUILD")

        if self.vol_timer > 0: self.vol_timer -= 1

    def draw_ixchel(self, surface, screen_x, screen_y):
        """Draws the agent as an Explorer character."""
        # Body
        pygame.draw.rect(surface, (139, 69, 19), (screen_x - 5, screen_y - 25, 10, 20)) 
        # Head
        pygame.draw.circle(surface, (210, 180, 140), (screen_x, screen_y - 32), 8)
        # Hat (Indiana Jones style)
        pygame.draw.ellipse(surface, (100, 70, 40), (screen_x - 12, screen_y - 42, 24, 8)) # Brim
        pygame.draw.rect(surface, (100, 70, 40), (screen_x - 7, screen_y - 46, 14, 8)) # Top

    def draw(self):
        self.grid.draw(self.screen)
        
        if self.mode == "BUILD":
            self.editor.draw(self.screen)
            self.draw_hud()
            
        elif self.mode == "ANALYSIS":
            self.draw_analysis_results()
            if self.ghost_agent.active:
                sx, sy = self.grid.world_to_screen(self.ghost_agent.x, self.ghost_agent.y)
                self.draw_ixchel(self.screen, sx, sy)
            self.draw_analysis_legend()

        self.toolbar.draw(self.screen)
        self.graph.draw(self.screen)
        self.prop_menu.draw(self.screen)
        
        # Messages / Toasts
        msg_text = None
        msg_color = COLOR_TEXT_MAIN
        if self.error_message:
            msg_text = self.error_message
            msg_color = (255, 80, 80)
        elif self.status_message:
            msg_text = self.status_message
            msg_color = (100, 255, 100)
            
        if msg_text:
            text = self.large_font.render(msg_text, True, msg_color)
            # Text background pill
            bg = pygame.Surface((text.get_width()+40, text.get_height()+20))
            bg.set_alpha(200)
            bg.fill((20, 20, 20))
            
            rect = text.get_rect(center=(self.screen.get_width()//2, 100))
            bg_rect = bg.get_rect(center=(self.screen.get_width()//2, 100))
            
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, bg_rect, 2, border_radius=10)
            self.screen.blit(bg, bg_rect)
            self.screen.blit(text, rect)
        
        # Controls Hint
        if self.mode == "BUILD":
            help_str = "SPACE: Szimuláció | TAB: Tömör/Üreges | M: Menü | G: Grafikon"
            help_txt = self.font.render(help_str, True, (80, 90, 80))
            self.screen.blit(help_txt, (self.screen.get_width() - help_txt.get_width() - 20, 20))
        
        self.draw_volume_popup()
        pygame.display.flip()

    def draw_analysis_legend(self):
        """Draws the explanation for Red/Blue colors."""
        box_w, box_h = 220, 100
        x = 20
        y = self.screen.get_height() - 420 
        
        s = pygame.Surface((box_w, box_h))
        s.set_alpha(230)
        s.fill((30, 35, 30))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, box_w, box_h), 2)
        
        font = pygame.font.SysFont("arial", 14, bold=True)
        title = font.render("Jelmagyarázat", True, COLOR_TEXT_HIGHLIGHT)
        self.screen.blit(title, (x + 10, y + 10))
        
        # Compression
        pygame.draw.rect(self.screen, COLOR_COMPRESSION, (x + 10, y + 35, 20, 20))
        lbl_c = font.render("Nyomás (Compression)", True, (200, 200, 200))
        self.screen.blit(lbl_c, (x + 40, y + 35))

        # Tension
        pygame.draw.rect(self.screen, COLOR_TENSION, (x + 10, y + 65, 20, 20))
        lbl_t = font.render("Húzás (Tension)", True, (200, 200, 200))
        self.screen.blit(lbl_t, (x + 40, y + 65))

    def draw_analysis_results(self):
         if not self.static_solver: return
         
         view_mode = self.prop_menu.view_mode 
         text_mode = self.prop_menu.text_mode
         
         # Draw Nodes first
         for node in self.bridge.nodes:
            pos = self.grid.world_to_screen(node.x, node.y)
            color = (180, 50, 50) if node.fixed else (80, 80, 80)
            pygame.draw.circle(self.screen, color, pos, 5)

         # Draw Beams
         for beam, force in self.static_solver.results.items():
            start = self.grid.world_to_screen(beam.node_a.x, beam.node_a.y)
            end = self.grid.world_to_screen(beam.node_b.x, beam.node_b.y)
            
            color = (100, 100, 100)
            
            props = MaterialManager.get_properties(beam.type, beam.hollow)
            thickness = props['thickness']
            width = max(2, int(thickness * PPM))
            
            capacity = props["E"] * props["strength"]
            ratio = abs(force) / capacity
            
            # STRESS VIEW
            if view_mode == 0: 
                # Negative force = Compression (Blue), Positive = Tension (Red)
                if force < 0: color = COLOR_COMPRESSION 
                else:         color = COLOR_TENSION
            
            # TEXTURE VIEW
            elif view_mode == 1: 
                color = beam.color
                
            # GRADIENT VIEW
            elif view_mode == 2: 
                if beam in self.broken_beams:
                    color = COLOR_BROKEN
                else:
                    base_c = beam.color
                    target_c = (255, 50, 50) # Red warning
                    t = min(1.0, ratio) 
                    r = int(base_c[0] + (target_c[0] - base_c[0]) * t)
                    g = int(base_c[1] + (target_c[1] - base_c[1]) * t)
                    b = int(base_c[2] + (target_c[2] - base_c[2]) * t)
                    color = (r, g, b)

            pygame.draw.line(self.screen, color, start, end, width)
            
            if beam.hollow:
                 inner_w = max(1, width - 4)
                 pygame.draw.line(self.screen, (255,255,255), start, end, inner_w)

            # Text Overlay
            if text_mode != 2: 
                mx = (start[0] + end[0]) // 2
                my = (start[1] + end[1]) // 2
                
                label = ""
                if text_mode == 0: label = f"{int(abs(force))}N"
                elif text_mode == 1: label = f"{int(ratio * 100)}%"
                    
                text = self.font.render(label, True, (255, 255, 255))
                # Small text background
                bg_rect = text.get_rect(center=(mx, my))
                bg_rect.inflate_ip(8, 4)
                pygame.draw.rect(self.screen, (20, 20, 20), bg_rect, border_radius=4)
                pygame.draw.rect(self.screen, color, bg_rect, 1, border_radius=4)
                self.screen.blit(text, text.get_rect(center=(mx, my)))

    def draw_volume_popup(self):
            if self.vol_timer <= 0: return
            w, h = self.screen.get_size()
            box_w, box_h = 220, 60
            margin = 30
            x = w - box_w - margin
            y = h - box_h - margin
            
            alpha = 230
            if self.vol_timer < 20: alpha = int(230 * (self.vol_timer / 20))
            
            s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(s, (30, 35, 30, alpha), (0,0,box_w,box_h), border_radius=10)
            pygame.draw.rect(s, (*COLOR_UI_BORDER, alpha), (0,0,box_w,box_h), 2, border_radius=10)
            
            bar_w = 180
            bar_h = 8
            bx = (box_w - bar_w)//2
            by = 35
            
            pygame.draw.rect(s, (50, 60, 50, alpha), (bx, by, bar_w, bar_h), border_radius=4)
            cw = int(bar_w * self.vol_display_val)
            if cw > 0:
                pygame.draw.rect(s, (100, 200, 255, alpha), (bx, by, cw, bar_h), border_radius=4)

            txt = self.font.render(f"Hangerő: {int(self.vol_display_val * 100)}%", True, COLOR_TEXT_MAIN)
            txt.set_alpha(alpha)
            s.blit(txt, (box_w//2 - txt.get_width()//2, 10))
            self.screen.blit(s, (x, y))

    def draw_hud(self):
        # Top-left info
        info = f"Csomópontok: {len(self.bridge.nodes)} | Elemek: {len(self.bridge.beams)}"
        text = self.font.render(info, True, COLOR_AXIS)
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