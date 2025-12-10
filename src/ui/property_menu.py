import pygame
from core.constants import *
from core.material_manager import MaterialManager

class Button:
    def __init__(self, label, rect, callback):
        self.label = label
        self.rect = rect
        self.callback = callback
        self.hover = False

    def update(self, mouse_pos, mouse_down, mouse_click):
        self.hover = self.rect.collidepoint(mouse_pos)
        if self.hover and mouse_click:
            self.callback()

    def draw(self, surface):
        # Stone button style
        color = (70, 80, 70) if self.hover else (50, 60, 50)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        
        border_col = COLOR_UI_BORDER if self.hover else (120, 120, 120)
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)
        
        font = pygame.font.SysFont("arial", 13, bold=True)
        txt = font.render(self.label, True, COLOR_TEXT_MAIN)
        tx = self.rect.centerx - txt.get_width() // 2
        ty = self.rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

class Slider:
    def __init__(self, label, unit, min_v, max_v, parent_dict, dict_key):
        self.label = label
        self.unit = unit # e.g. "kg", "N"
        self.min_v = min_v
        self.max_v = max_v
        self.parent_dict = parent_dict 
        self.dict_key = dict_key       
        self.dragging = False

    def update(self, rect, mouse_pos, mouse_down):
        mx, my = mouse_pos
        
        if mouse_down:
            if rect.collidepoint(mx, my) or self.dragging:
                self.dragging = True
                ratio = (mx - rect.x) / rect.width
                ratio = max(0.0, min(1.0, ratio))
                new_val = self.min_v + ratio * (self.max_v - self.min_v)
                self.parent_dict[self.dict_key] = new_val
        else:
            self.dragging = False

    def draw(self, surface, rect):
        curr = self.parent_dict[self.dict_key]
        
        # Label above slider
        font = pygame.font.SysFont("arial", 12)
        val_str = f"{curr:.2f} {self.unit}"
        label_txt = font.render(f"{self.label}", True, (200, 200, 200))
        val_txt = font.render(val_str, True, COLOR_TEXT_HIGHLIGHT)
        
        surface.blit(label_txt, (rect.x, rect.y - 18))
        surface.blit(val_txt, (rect.right - val_txt.get_width(), rect.y - 18))

        # Slider Track
        pygame.draw.rect(surface, (30, 30, 30), rect, border_radius=4)
        
        # Slider Fill
        ratio = (curr - self.min_v) / (self.max_v - self.min_v)
        fill_w = int(rect.width * ratio)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, (100, 150, 100), fill_rect, border_radius=4)
        
        # Handle (Gold Knob)
        handle_x = rect.x + fill_w
        pygame.draw.circle(surface, COLOR_UI_BORDER, (handle_x, rect.centery), 6)

class PropertyMenu:
    def __init__(self, screen_w, screen_h):
        self.w = 280
        self.h = screen_h
        self.x = screen_w - self.w
        self.y = 0
        self.visible = False
        self.should_quit = False
        
        self.sliders = []
        self.buttons = []
        
        # View Modes
        self.view_mode = 1 # 0=Stress, 1=Texture, 2=Gradient
        self.text_mode = 0 # 0=Value, 1=Percent, 2=None
        
        self.setup_ui()

    def setup_ui(self):
        # Translations to Hungarian
        # Wood -> Fa
        self.sliders.append(Slider("Fa Merevség (E)", "GPa", 100, 5000, MaterialManager.MATERIALS["wood"], "E"))
        self.sliders.append(Slider("Fa Sűrűség", "kg/m", 0.1, 5.0, MaterialManager.MATERIALS["wood"], "density"))
        self.sliders.append(Slider("Fa Teherbírás", "N", 0.001, 0.2, MaterialManager.MATERIALS["wood"], "strength"))
        self.sliders.append(Slider("Fa Vastagság", "m", 0.01, 0.5, MaterialManager.MATERIALS["wood"], "thickness"))
        
        # Bamboo -> Bambusz
        self.sliders.append(Slider("Bambusz Merevség", "GPa", 100, 5000, MaterialManager.MATERIALS["bamboo"], "E"))
        self.sliders.append(Slider("Bambusz Sűrűség", "kg/m", 0.1, 5.0, MaterialManager.MATERIALS["bamboo"], "density"))
        self.sliders.append(Slider("Bambusz Teherbírás", "N", 0.001, 0.5, MaterialManager.MATERIALS["bamboo"], "strength"))
        self.sliders.append(Slider("Bambusz Vastagság", "m", 0.01, 0.5, MaterialManager.MATERIALS["bamboo"], "thickness"))

        # Vine -> Inda
        self.sliders.append(Slider("Inda Merevség", "GPa", 10, 500, MaterialManager.MATERIALS["vine"], "E"))
        self.sliders.append(Slider("Inda Sűrűség", "kg/m", 0.1, 5.0, MaterialManager.MATERIALS["vine"], "density"))
        self.sliders.append(Slider("Inda Teherbírás", "N", 0.01, 1.0, MaterialManager.MATERIALS["vine"], "strength"))
        self.sliders.append(Slider("Inda Vastagság", "m", 0.01, 0.3, MaterialManager.MATERIALS["vine"], "thickness"))

        # Agent -> Ixchel
        self.sliders.append(Slider("Ixchel Tömege", "kg", 1.0, 500.0, MaterialManager.AGENT, "mass"))
        self.sliders.append(Slider("Ixchel Sebessége", "m/s", 1.0, 20.0, MaterialManager.AGENT, "speed"))

        # --- Buttons ---
        # Adjusted spacing
        start_y = 60 + len(self.sliders) * 42 + 20
        btn_w = 220
        btn_h = 35
        
        r1 = pygame.Rect(self.x + 30, start_y, btn_w, btn_h)
        self.buttons.append(Button("Nézet Váltása (V)", r1, self.toggle_view_mode))
        
        r2 = pygame.Rect(self.x + 30, start_y + 45, btn_w, btn_h)
        self.buttons.append(Button("Feliratok Váltása (T)", r2, self.toggle_text_mode))
        
        r_quit = pygame.Rect(self.x + 30, self.h - 80, btn_w, btn_h)
        self.buttons.append(Button("Kilépés", r_quit, self.trigger_quit))

    def trigger_quit(self):
        self.should_quit = True

    def toggle_view_mode(self):
        self.view_mode = (self.view_mode + 1) % 3

    def toggle_text_mode(self):
        self.text_mode = (self.text_mode + 1) % 3

    def toggle(self):
        self.visible = not self.visible

    def handle_input(self, event):
        if not self.visible: return False
        
        mx, my = pygame.mouse.get_pos()
        
        if mx > self.x:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    if btn.rect.collidepoint(mx, my):
                        btn.callback()
            return True 
        return False

    def update(self):
        if not self.visible: return
        
        mx, my = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        
        start_y = 60
        gap = 42
        
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 30, start_y + i*gap, 220, 12)
            slider.update(rect, (mx, my), mouse_down)
            
        for btn in self.buttons:
            btn.update((mx, my), mouse_down, False)

    def draw(self, surface):
        if not self.visible: return
        
        # Panel Background
        s = pygame.Surface((self.w, self.h))
        s.set_alpha(240)
        s.fill((35, 40, 35))
        surface.blit(s, (self.x, self.y))
        
        # Decorative Left Border
        pygame.draw.line(surface, COLOR_UI_BORDER, (self.x, 0), (self.x, self.h), 3)
        
        # Header
        font = pygame.font.SysFont("arial", 20, bold=True)
        h = font.render("Tulajdonságok", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(h, (self.x + 30, 20))
        
        # Draw Sliders
        start_y = 60
        gap = 42
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 30, start_y + i*gap, 220, 12)
            slider.draw(surface, rect)
            
        # Draw Buttons
        for btn in self.buttons:
            btn.draw(surface)
            
        # Status Info
        info_font = pygame.font.SysFont("arial", 12)
        
        # Translated View Modes
        v_modes = ["Erők (Kék/Piros)", "Anyagminta (Normál)", "Terhelés (Gradiens)"]
        v_str = f"Nézet: {v_modes[self.view_mode]}"
        v_txt = info_font.render(v_str, True, (180, 200, 180))
        surface.blit(v_txt, (self.x + 30, self.buttons[1].rect.bottom + 10))

        t_modes = ["Pontos Érték", "% Terhelés", "Nincs"]
        t_str = f"Adat: {t_modes[self.text_mode]}"
        t_txt = info_font.render(t_str, True, (180, 200, 180))
        surface.blit(t_txt, (self.x + 30, self.buttons[1].rect.bottom + 25))
            
        mode = "ÜREGES (Cső)" if MaterialManager.PLACEMENT_MODE_HOLLOW else "TÖMÖR (Rúd)"
        col = (100, 255, 100) if not MaterialManager.PLACEMENT_MODE_HOLLOW else (100, 200, 255)
        
        txt = info_font.render(f"Építési Mód: {mode}", True, col)
        surface.blit(txt, (self.x + 30, self.h - 110))