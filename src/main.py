import pygame
import sys
import math
import numpy as np
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
        self.graph = GraphOverlay(20, h - 300, 300, 150)
        self.prop_menu = PropertyMenu(w, h)
        
        self.mode = "BUILD"
        self.static_solver = None
        self.broken_beams = set()
        self.simulation_frozen = False # Flag to freeze simulation on break
        
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
        self.audio.load_sfx("wood_break", "wood_break.mp3")
        self.audio.load_sfx("vine_break", "vine_break.mp3")

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
                
                # Hotkeys
                if event.key == pygame.K_v: 
                    self.prop_menu.toggle_view_mode()
                if event.key == pygame.K_t: 
                    self.prop_menu.toggle_text_mode()
                
                if event.key == pygame.K_SPACE:
                    if self.mode == "BUILD": 
                        self.run_static_analysis()
                    elif self.mode == "ANALYSIS": 
                        self.stop_analysis()
                    continue

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
            if not self.simulation_frozen:
                self.ghost_agent.handle_input()

    def run_static_analysis(self):
        self.ghost_agent.mass = MaterialManager.AGENT["mass"]
        solver = StaticSolver(self.bridge)
        if not solver.is_stable():
            if "Mechanism" in solver.error_msg:
                self.show_error("Instabil szerkezet! (Mechanizmus)")
            else:
                self.show_error(solver.error_msg)
            return
        
        success = solver.solve(temperature=0.0, point_load=None)
        if not success:
            self.show_error("Instabil: Szinguláris Mátrix")
        else:
            self.static_solver = solver
            self.mode = "ANALYSIS"
            self.simulation_frozen = False
            self.show_status(f"Szimuláció (Tömeg: {self.ghost_agent.mass:.1f}kg)")
            self.graph.reset_data()
            self.broken_beams.clear()
            self.graph.visible = True
            
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
        self.simulation_frozen = False
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

        max_force_val = 0.0
        max_perc = 0.0
        
        if self.mode == "ANALYSIS" and self.static_solver:
            if self.simulation_frozen:
                return

            self.ghost_agent.mass = MaterialManager.AGENT["mass"]
            # Use the same exaggeration factor as the renderer (20.0)
            disps = self.static_solver.displacements
            
            # Pass displacements and exaggeration to the agent
            load_info = self.ghost_agent.update_static(1.0/60.0, self.bridge.beams, disps, EXAGGERATION)
            
            delta_T = MaterialManager.SETTINGS["sim_temp"] - MaterialManager.SETTINGS["base_temp"]
            self.static_solver.solve(temperature=delta_T, point_load=load_info)
            
            new_break = False
            for beam in self.bridge.beams:
                f_axial = abs(self.static_solver.results.get(beam, 0))
                f_bend = abs(self.static_solver.bending_results.get(beam, 0))
                
                total_load_N = f_axial + f_bend
                
                if total_load_N > max_force_val: 
                    max_force_val = total_load_N
                
                ratio = self.static_solver.stress_ratios.get(beam, 0)
                pct = ratio * 100.0
                
                if pct > max_perc: max_perc = pct
                
                if ratio >= 1.0: 
                    if beam not in self.broken_beams:
                        self.broken_beams.add(beam)
                        new_break = True
            
            if new_break:
                self.simulation_frozen = True
                self.show_error("HÍDSZAKADÁS! (Szimuláció Megállítva)")
                if any(b.type == "vine" for b in self.broken_beams):
                     self.audio.play_sfx("vine_break")
                else:
                     self.audio.play_sfx("wood_break")
                self.audio.stop_sfx("step")
            
            self.graph.update(max_force_val, max_perc, "ANALYSIS")
        else:
            self.graph.update(0, 0, "BUILD")

        if self.vol_timer > 0: self.vol_timer -= 1

    def draw_ixchel(self, surface, screen_x, screen_y):
        pygame.draw.rect(surface, (139, 69, 19), (screen_x - 5, screen_y - 25, 10, 20)) 
        pygame.draw.circle(surface, (210, 180, 140), (screen_x, screen_y - 32), 8)
        pygame.draw.ellipse(surface, (100, 70, 40), (screen_x - 12, screen_y - 42, 24, 8)) 
        pygame.draw.rect(surface, (100, 70, 40), (screen_x - 7, screen_y - 46, 14, 8)) 

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
            bg = pygame.Surface((text.get_width()+40, text.get_height()+20))
            bg.set_alpha(200)
            bg.fill((20, 20, 20))
            
            rect = text.get_rect(center=(self.screen.get_width()//2, 100))
            bg_rect = bg.get_rect(center=(self.screen.get_width()//2, 100))
            
            pygame.draw.rect(self.screen, COLOR_UI_BORDER, bg_rect, 2, border_radius=10)
            self.screen.blit(bg, bg_rect)
            self.screen.blit(text, rect)
        
        if self.mode == "BUILD":
            help_str = "SPACE: Szimuláció | M: Menü | G: Grafikon"
            help_txt = self.font.render(help_str, True, (80, 90, 80))
            self.screen.blit(help_txt, (self.screen.get_width() - help_txt.get_width() - 20, 20))
        
        self.draw_volume_popup()
        pygame.display.flip()

    def draw_analysis_legend(self):
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
        
        pygame.draw.rect(self.screen, COLOR_COMPRESSION, (x + 10, y + 35, 20, 20))
        lbl_c = font.render("Nyomás (Compression)", True, (200, 200, 200))
        self.screen.blit(lbl_c, (x + 40, y + 35))

        pygame.draw.rect(self.screen, COLOR_TENSION, (x + 10, y + 65, 20, 20))
        lbl_t = font.render("Húzás (Tension)", True, (200, 200, 200))
        self.screen.blit(lbl_t, (x + 40, y + 65))

    def draw_analysis_results(self):
         if not self.static_solver: return
         
         view_mode = self.prop_menu.view_mode 
         text_mode = self.prop_menu.text_mode
         
         # 1. Draw Nodes
         for node in self.bridge.nodes:
            dx, dy, _ = self.static_solver.displacements.get(node, (0,0,0))
            def_x = node.x + dx * EXAGGERATION
            def_y = node.y + dy * EXAGGERATION
            pos = self.grid.world_to_screen(def_x, def_y)
            color = (180, 50, 50) if node.fixed else (80, 80, 80)
            pygame.draw.circle(self.screen, color, pos, 5)

         # 2. Draw Beams (Curved)
         for beam, force in self.static_solver.results.items():
            da_x, da_y, da_theta = self.static_solver.displacements.get(beam.node_a, (0,0,0))
            db_x, db_y, db_theta = self.static_solver.displacements.get(beam.node_b, (0,0,0))
            
            p1_x = beam.node_a.x + da_x * EXAGGERATION
            p1_y = beam.node_a.y + da_y * EXAGGERATION
            p2_x = beam.node_b.x + db_x * EXAGGERATION
            p2_y = beam.node_b.y + db_y * EXAGGERATION
            
            chord_dx = p2_x - p1_x
            chord_dy = p2_y - p1_y
            L_deformed = math.hypot(chord_dx, chord_dy)
            psi = math.atan2(chord_dy, chord_dx)
            
            orig_dx = beam.node_b.x - beam.node_a.x
            orig_dy = beam.node_b.y - beam.node_a.y
            alpha = math.atan2(orig_dy, orig_dx)
            
            rot1 = (alpha + da_theta * EXAGGERATION) - psi
            rot2 = (alpha + db_theta * EXAGGERATION) - psi
            
            points = []
            segments = 12 
            for i in range(segments + 1):
                s = i / segments 
                h1 = s**3 - 2*s**2 + s
                h2 = s**3 - s**2
                v = L_deformed * (h1 * rot1 + h2 * rot2)
                u = s * L_deformed 
                cp = math.cos(psi)
                sp = math.sin(psi)
                wx = p1_x + u*cp - v*sp
                wy = p1_y + u*sp + v*cp
                points.append(self.grid.world_to_screen(wx, wy))

            color = (100, 100, 100)
            
            props = MaterialManager.get_properties(beam.type)
            width = max(2, int(props['thickness'] * PPM))
            
            mat_settings = MaterialManager.MATERIALS.get(beam.type, {})
            hollow_ratio = mat_settings.get("hollow_ratio", 0.0)
            
            ratio = self.static_solver.stress_ratios.get(beam, 0.0)
            
            # --- COLORING LOGIC ---
            if beam in self.broken_beams:
                 # Draw Red/Black stripes
                 if len(points) > 1:
                    for i in range(len(points) - 1):
                        p_start = points[i]
                        p_end = points[i+1]
                        # Alternate colors: Red and Black
                        seg_color = (255, 0, 0) if (i % 2 == 0) else (0, 0, 0)
                        pygame.draw.line(self.screen, seg_color, p_start, p_end, width)
            else:
                if view_mode == 0: 
                    if force < 0: color = COLOR_COMPRESSION 
                    else:         color = COLOR_TENSION
                elif view_mode == 1: 
                    color = beam.color
                elif view_mode == 2: 
                    base_c = beam.color
                    target_c = (255, 50, 50)
                    t = min(1.0, ratio) 
                    r = int(base_c[0] + (target_c[0] - base_c[0]) * t)
                    g = int(base_c[1] + (target_c[1] - base_c[1]) * t)
                    b = int(base_c[2] + (target_c[2] - base_c[2]) * t)
                    color = (r, g, b)

                if len(points) > 1:
                    pygame.draw.lines(self.screen, color, False, points, width)
            
            # White hollow inner line (only if not completely solid)
            if hollow_ratio > 0.01 and len(points) > 1:
                 inner_w = max(1, int(width * hollow_ratio))
                 pygame.draw.lines(self.screen, (255,255,255), False, points, inner_w)

            if text_mode != 2: 
                mid_idx = segments // 2
                mx, my = points[mid_idx]
                label = ""
                if text_mode == 0: 
                    bend = abs(self.static_solver.bending_results.get(beam, 0))
                    label = f"{int(abs(force))}N | {int(bend)}N"
                elif text_mode == 1: 
                    label = f"{int(ratio * 100)}%"
                    
                text = self.font.render(label, True, (255, 255, 255))
                bg_rect = text.get_rect(center=(mx, my))
                bg_rect.inflate_ip(8, 4)
                pygame.draw.rect(self.screen, (20, 20, 20), bg_rect, border_radius=4)
                pygame.draw.rect(self.screen, color, bg_rect, 1, border_radius=4)
                self.screen.blit(text, text.get_rect(center=(mx, my)))

    def draw_hud(self):
        info = f"Csomópontok: {len(self.bridge.nodes)} | Elemek: {len(self.bridge.beams)}"
        text = self.font.render(info, True, COLOR_AXIS)
        self.screen.blit(text, (20, 20))

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