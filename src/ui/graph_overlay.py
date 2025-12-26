import pygame
from core.constants import *
from ui.property_menu import Slider

class GraphOverlay:
    def __init__(self, x, y, width, height, settings_dict=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.history = [] 
        self.max_len = width - 40  # Reduced width slightly to make room for right-side text
        self.visible = False
        self.eng_max_force = 100.0 # Tracks only Force peaks now

        # Initialize Slider
        self.sim_settings = settings_dict if settings_dict else {"exaggeration": 100.0}
        self.slider = None
        if self.sim_settings is not None:
             # Slider positioned 10px below the graph
             self.slider_rect = pygame.Rect(x, y + height + 20, width, 14)
             # Log scale slider: Min 1, Max 1000, Default 100 is perfectly in middle if Log
             self.slider = Slider("Torzítás (Exaggeration)", "x", 1.0, 1000.0, self.sim_settings, "exaggeration", is_log=True)

    def toggle(self):
        self.visible = not self.visible
    
    def reset_data(self):
        self.history = []
        self.eng_max_force = 100.0

    def update(self, force_val, percent_val, mode):
        if not self.visible: return
        
        # Append data
        self.history.append((force_val, percent_val, mode))
        if len(self.history) > self.max_len:
            self.history.pop(0)

        # Update dynamic scale for FORCE only
        if mode == "ANALYSIS":
            if force_val > self.eng_max_force: 
                self.eng_max_force = force_val
                
    def handle_input(self, event):
        """Processes input events (though Slider mainly uses continuous state in draw)."""
        if not self.visible or not self.slider: return
        
        # Slider logic is typically driven by update() loops in this codebase's style,
        # but here we can just update it based on current mouse state
        mx, my = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        
        # We manually update the slider state here
        self.slider.update(self.slider_rect, (mx, my), mouse_down)

    def draw(self, surface):
        if not self.visible: return

        # --- Background ---
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(230)
        s.fill((20, 25, 20))
        surface.blit(s, self.rect)
        
        # --- Border ---
        pygame.draw.rect(surface, COLOR_UI_BORDER, self.rect, 2)
        
        # --- Grid Lines (Fixed 0%, 25%, 50%, 75%, 100%) ---
        font_axis = pygame.font.SysFont("arial", 10)
        
        graph_top = self.rect.y + 20
        graph_bot = self.rect.bottom - 20
        graph_h = graph_bot - graph_top

        for i in range(5): # 0, 1, 2, 3, 4
            ratio = i / 4.0 # 0.0, 0.25, 0.5, 0.75, 1.0
            y_pos = graph_bot - (graph_h * ratio)
            
            # Dotted or dim line
            color = (60, 70, 60) if i > 0 else (0,0,0)
            if i > 0:
                pygame.draw.line(surface, color, (self.rect.x, y_pos), (self.rect.right, y_pos), 1)
            
            # Right Axis Labels (Percentage)
            label_txt = f"{int(ratio * 100)}%"
            txt_surf = font_axis.render(label_txt, True, (80, 160, 80))
            # Align to right edge
            surface.blit(txt_surf, (self.rect.right - 25, y_pos - 6))

        if not self.history: 
            # "No Data" text
            font = pygame.font.SysFont("arial", 14)
            txt = font.render("Várakozás adatokra...", True, (100, 100, 100))
            surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery))
        else:
            # --- Plotting ---
            y_max_force = self.eng_max_force if self.eng_max_force > 1 else 100.0
            
            points_force = []
            points_load = []
            
            start_x = self.rect.x + 5

            for i, (f_val, p_val, mode) in enumerate(self.history):
                if mode != "ANALYSIS": continue

                px = start_x + i
                
                # 1. Force Y Calculation (Dynamic Scale)
                norm_f = min(1.0, f_val / y_max_force)
                py_f = graph_bot - (norm_f * graph_h)
                
                # 2. Percent Y Calculation (Fixed 0-100 Scale)
                norm_p = p_val / 100.0 
                py_p = graph_bot - (norm_p * graph_h)
                
                # Clamp visuals to stay inside box
                py_f = max(self.rect.y, min(self.rect.bottom, py_f))
                py_p = max(self.rect.y, min(self.rect.bottom, py_p))

                points_force.append((px, py_f))
                points_load.append((px, py_p))

            # Draw Lines (Anti-aliased)
            if len(points_force) > 1:
                pygame.draw.aalines(surface, COLOR_TENSION, False, points_force)
            if len(points_load) > 1:
                pygame.draw.aalines(surface, (100, 255, 100), False, points_load)

            # --- HUD / Legend ---
            font_legend = pygame.font.SysFont("arial", 12, bold=True)
            
            # Left Axis Max Label (Force)
            top_force_txt = f"{int(y_max_force)} N"
            surface.blit(font_legend.render(top_force_txt, True, COLOR_TENSION), (self.rect.x + 5, graph_top - 15))
            
            # Legend Texts
            lbl_force = font_legend.render("Erő (N)", True, COLOR_TENSION)
            lbl_perc = font_legend.render("Terhelés (%)", True, (100, 255, 100))
            
            surface.blit(lbl_force, (self.rect.x + 5, self.rect.bottom - 45))
            surface.blit(lbl_perc, (self.rect.x + 5, self.rect.bottom - 25))
            
            # Current Real-time Values (Bottom Right)
            curr_force = self.history[-1][0]
            curr_perc = self.history[-1][1]
            
            val_f = font_legend.render(f"{int(curr_force)}", True, COLOR_TENSION)
            val_p = font_legend.render(f"{int(curr_perc)}", True, (100, 255, 100))
            
            surface.blit(val_f, (self.rect.x + 60, self.rect.bottom - 45))
            surface.blit(val_p, (self.rect.x + 90, self.rect.bottom - 25))

        # --- Draw Slider (Below Graph) ---
        if self.slider:
            self.slider.draw(surface, self.slider_rect)