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
        self.unit = unit 
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
        curr = self.parent_dict.get(self.dict_key, 0.0)
        
        display_val = curr
        display_unit = self.unit
        
        if self.dict_key == "E": 
            display_val = curr / 1e9
            display_unit = "GPa"
        elif self.dict_key == "strength": 
            display_val = curr / 1e6
            display_unit = "MPa"
        elif self.dict_key == "hollow_ratio":
            display_val = curr * 100.0
            display_unit = "%"
            
        font = pygame.font.SysFont("arial", 12)
        val_str = f"{display_val:.1f} {display_unit}"
        
        label_txt = font.render(f"{self.label}", True, (200, 200, 200))
        val_txt = font.render(val_str, True, COLOR_TEXT_HIGHLIGHT)
        
        surface.blit(label_txt, (rect.x, rect.y - 18))
        surface.blit(val_txt, (rect.right - val_txt.get_width(), rect.y - 18))

        pygame.draw.rect(surface, (30, 30, 30), rect, border_radius=4)
        
        try:
            ratio = (curr - self.min_v) / (self.max_v - self.min_v)
            ratio = max(0.0, min(1.0, ratio))
        except ZeroDivisionError:
            ratio = 0.0

        fill_w = int(rect.width * ratio)
        fill_rect = (rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, (100, 150, 100), fill_rect, border_radius=4)
        
        handle_x = rect.x + fill_w
        pygame.draw.circle(surface, COLOR_UI_BORDER, (handle_x, rect.centery), 6)

class PropertyMenu:
    def __init__(self, screen_w, screen_h):
        self.w = 300 
        self.h = screen_h
        self.x = screen_w - self.w
        self.y = 0
        self.visible = False
        self.should_quit = False
        
        self.sliders = []
        self.buttons = []
        self.temp_slider = None 
        
        self.view_mode = 1 
        self.text_mode = 0 
        
        self.setup_ui()

    def set_analysis_mode(self, enabled):
        if enabled:
            self.temp_slider.dict_key = "sim_temp"
            self.temp_slider.label = "Szim. Hőm."
        else:
            self.temp_slider.dict_key = "base_temp"
            self.temp_slider.label = "Alap Hőm."

    def create_centered_slider(self, label, unit, mat_key, prop_key, range_percent=0.5):
        default_val = MaterialManager.MATERIALS[mat_key][prop_key]
        min_v = default_val * (1.0 - range_percent)
        max_v = default_val * (1.0 + range_percent)
        self.sliders.append(Slider(label, unit, min_v, max_v, MaterialManager.MATERIALS[mat_key], prop_key))

    def setup_ui(self):
        # --- FA ---
        self.create_centered_slider("Fa Rugalmasság (E)", "Pa", "wood", "E")
        self.create_centered_slider("Fa Sűrűség", "kg/m³", "wood", "density")
        self.create_centered_slider("Fa Szakítószilárdság", "Pa", "wood", "strength")
        self.sliders.append(Slider("Fa Átmérő", "m", 0.05, 0.5, MaterialManager.MATERIALS["wood"], "thickness"))
        self.sliders.append(Slider("Fa Üregesség", "%", 0.0, 0.99, MaterialManager.MATERIALS["wood"], "hollow_ratio"))
        
        # --- BAMBUSZ ---
        self.create_centered_slider("Bambusz Rugalmasság", "Pa", "bamboo", "E")
        self.create_centered_slider("Bambusz Sűrűség", "kg/m³", "bamboo", "density")
        self.create_centered_slider("Bambusz Szakítószil.", "Pa", "bamboo", "strength")
        self.sliders.append(Slider("Bambusz Átmérő", "m", 0.02, 0.3, MaterialManager.MATERIALS["bamboo"], "thickness"))
        self.sliders.append(Slider("Bambusz Üregesség", "%", 0.0, 0.99, MaterialManager.MATERIALS["bamboo"], "hollow_ratio"))

        # --- INDA ---
        self.create_centered_slider("Inda Rugalmasság", "Pa", "vine", "E")
        self.create_centered_slider("Inda Sűrűség", "kg/m³", "vine", "density")
        self.create_centered_slider("Inda Szakítószil.", "Pa", "vine", "strength")
        self.sliders.append(Slider("Inda Átmérő", "m", 0.01, 0.15, MaterialManager.MATERIALS["vine"], "thickness"))
        self.sliders.append(Slider("Inda Üregesség", "%", 0.0, 0.99, MaterialManager.MATERIALS["vine"], "hollow_ratio"))

        # --- GLOBALS ---
        # Temperature Slider (Context sensitive)
        self.temp_slider = Slider("Alap Hőm.", "°C", 0.0, 50.0, MaterialManager.SETTINGS, "base_temp")
        self.sliders.append(self.temp_slider)

        # Agent
        self.sliders.append(Slider("Ixchel Tömege", "kg", 40.0, 150.0, MaterialManager.AGENT, "mass")) 
        self.sliders.append(Slider("Ixchel Sebessége", "m/s", 1.0, 10.0, MaterialManager.AGENT, "speed"))

        # --- Buttons ---
        start_y = 60 + len(self.sliders) * 42 + 20
        btn_w = 240
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
            rect = pygame.Rect(self.x + 30, start_y + i*gap, 240, 12)
            slider.update(rect, (mx, my), mouse_down)
        for btn in self.buttons:
            btn.update((mx, my), mouse_down, False)

    def draw(self, surface):
        if not self.visible: return
        
        s = pygame.Surface((self.w, self.h))
        s.set_alpha(240)
        s.fill((35, 40, 35))
        surface.blit(s, (self.x, self.y))
        
        pygame.draw.line(surface, COLOR_UI_BORDER, (self.x, 0), (self.x, self.h), 3)
        
        font = pygame.font.SysFont("arial", 20, bold=True)
        h = font.render("Tulajdonságok", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(h, (self.x + 30, 20))
        
        start_y = 60
        gap = 42
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 30, start_y + i*gap, 240, 12)
            slider.draw(surface, rect)
            
        for btn in self.buttons:
            btn.draw(surface)
            
        info_font = pygame.font.SysFont("arial", 12)
        
        v_modes = ["Erők (Kék/Piros)", "Anyagminta (Normál)", "Terhelés (Gradiens)"]
        v_str = f"Nézet: {v_modes[self.view_mode]}"
        v_txt = info_font.render(v_str, True, (180, 200, 180))
        surface.blit(v_txt, (self.x + 30, self.buttons[1].rect.bottom + 10))

        t_modes = ["Pontos Érték", "% Terhelés", "Nincs"]
        t_str = f"Adat: {t_modes[self.text_mode]}"
        t_txt = info_font.render(t_str, True, (180, 200, 180))
        surface.blit(t_txt, (self.x + 30, self.buttons[1].rect.bottom + 25))