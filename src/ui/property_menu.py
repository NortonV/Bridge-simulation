import pygame
import math
from core.constants import *
from core.material_manager import MaterialManager

class Button:
    def __init__(self, label, rect, callback):
        self.label = label
        self.rect = rect
        self.callback = callback
        self.hover = False

    def update(self, mouse_pos, mouse_down, mouse_click, scroll_y=0):
        scrolled_rect = self.rect.move(0, -scroll_y)
        self.hover = scrolled_rect.collidepoint(mouse_pos)
        if self.hover and mouse_click:
            self.callback()

    def draw(self, surface, scroll_y=0):
        scrolled_rect = self.rect.move(0, -scroll_y)
        color = (70, 80, 70) if self.hover else (50, 60, 50)
        pygame.draw.rect(surface, color, scrolled_rect, border_radius=6)
        border_col = COLOR_UI_BORDER if self.hover else (120, 120, 120)
        pygame.draw.rect(surface, border_col, scrolled_rect, 2, border_radius=6)
        
        font = pygame.font.SysFont("arial", 13, bold=True)
        txt = font.render(self.label, True, COLOR_TEXT_MAIN)
        tx = scrolled_rect.centerx - txt.get_width() // 2
        ty = scrolled_rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

class Slider:
    def __init__(self, label, unit, min_v, max_v, parent_dict, dict_key, is_log=False):
        self.label = label
        self.unit = unit 
        self.min_v = min_v
        self.max_v = max_v
        self.parent_dict = parent_dict 
        self.dict_key = dict_key       
        self.dragging = False
        self.is_log = is_log

    def update(self, rect, mouse_pos, mouse_down):
        mx, my = mouse_pos
        if mouse_down:
            if rect.collidepoint(mx, my) or self.dragging:
                self.dragging = True
                ratio = (mx - rect.x) / rect.width
                ratio = max(0.0, min(1.0, ratio))
                
                if self.is_log:
                    # Logarithmic interpolation: val = min * (max/min)^ratio
                    safe_min = max(1e-9, self.min_v)
                    new_val = safe_min * (self.max_v / safe_min) ** ratio
                else:
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
        
        # High precision formatting for small values
        if abs(display_val) < 0.001:
            val_str = f"{display_val:.5f} {display_unit}"
        elif abs(display_val) < 0.1:
            val_str = f"{display_val:.3f} {display_unit}"
        elif abs(display_val) < 10.0:
            val_str = f"{display_val:.2f} {display_unit}"
        else:
            val_str = f"{display_val:.1f} {display_unit}"
        
        label_txt = font.render(f"{self.label}", True, (200, 200, 200))
        val_txt = font.render(val_str, True, COLOR_TEXT_HIGHLIGHT)
        
        surface.blit(label_txt, (rect.x, rect.y - 18))
        surface.blit(val_txt, (rect.right - val_txt.get_width(), rect.y - 18))

        pygame.draw.rect(surface, (30, 30, 30), rect, border_radius=4)
        
        ratio = 0.0
        try:
            if self.is_log:
                safe_min = max(1e-9, self.min_v)
                safe_curr = max(safe_min, curr)
                # ratio = log(curr/min) / log(max/min)
                num = math.log(safe_curr / safe_min)
                den = math.log(self.max_v / safe_min)
                ratio = num / den if den != 0 else 0
            else:
                ratio = (curr - self.min_v) / (self.max_v - self.min_v)
            
            ratio = max(0.0, min(1.0, ratio))
        except (ValueError, ZeroDivisionError):
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
        self.scrollable_buttons = []
        self.fixed_buttons = []
        self.temp_slider = None 
        
        self.view_mode = 1 
        self.text_mode = 0 
        
        self.scroll_y = 0
        self.scroll_area_top = 60
        self.scroll_area_bottom = self.h - 90
        self.content_padding_top = 30 
        self.content_padding_bottom = 40
        
        self.setup_ui()

    def set_analysis_mode(self, enabled):
        if enabled:
            self.temp_slider.dict_key = "sim_temp"
            self.temp_slider.label = "Szim. Hőm."
        else:
            self.temp_slider.dict_key = "base_temp"
            self.temp_slider.label = "Alap Hőm."

    def create_centered_slider(self, label, unit, mat_key, prop_key, factor=20.0):
        # Creates a Log-Scale slider centered on the default value
        # Min = Default / Factor
        # Max = Default * Factor
        default_val = MaterialManager.MATERIALS[mat_key][prop_key]
        min_v = default_val / factor
        max_v = default_val * factor
        self.sliders.append(Slider(label, unit, min_v, max_v, MaterialManager.MATERIALS[mat_key], prop_key, is_log=True))

    def setup_ui(self):
        # --- WOOD ---
        self.create_centered_slider("Fa Rugalmasság (E)", "Pa", "wood", "E", factor=20.0)
        self.create_centered_slider("Fa Sűrűség", "kg/m³", "wood", "density", factor=10.0)
        self.create_centered_slider("Fa Szakítószil.", "Pa", "wood", "strength", factor=20.0)
        
        d_thick = MaterialManager.MATERIALS["wood"]["thickness"]
        self.sliders.append(Slider("Fa Átmérő", "m", d_thick/20.0, d_thick*20.0, MaterialManager.MATERIALS["wood"], "thickness", is_log=True))
        self.sliders.append(Slider("Fa Üregesség", "%", 0.0, 0.99, MaterialManager.MATERIALS["wood"], "hollow_ratio"))
        
        # --- BAMBOO ---
        self.create_centered_slider("Bambusz Rugalmasság", "Pa", "bamboo", "E", factor=20.0)
        self.create_centered_slider("Bambusz Sűrűség", "kg/m³", "bamboo", "density", factor=10.0)
        self.create_centered_slider("Bambusz Szakítószil.", "Pa", "bamboo", "strength", factor=20.0)
        
        d_thick = MaterialManager.MATERIALS["bamboo"]["thickness"]
        self.sliders.append(Slider("Bambusz Átmérő", "m", d_thick/20.0, d_thick*20.0, MaterialManager.MATERIALS["bamboo"], "thickness", is_log=True))
        self.sliders.append(Slider("Bambusz Üregesség", "%", 0.0, 0.99, MaterialManager.MATERIALS["bamboo"], "hollow_ratio"))

        # --- STEEL ---
        self.create_centered_slider("Acél Rugalmasság", "Pa", "steel", "E", factor=20.0)
        self.create_centered_slider("Acél Sűrűség", "kg/m³", "steel", "density", factor=10.0)
        self.create_centered_slider("Acél Szakítószil.", "Pa", "steel", "strength", factor=20.0)
        
        d_thick = MaterialManager.MATERIALS["steel"]["thickness"]
        self.sliders.append(Slider("Acél Átmérő", "m", d_thick/20.0, d_thick*20.0, MaterialManager.MATERIALS["steel"], "thickness", is_log=True))

        # --- SPAGHETTI ---
        self.create_centered_slider("Spagetti Rugalmasság", "Pa", "spaghetti", "E", factor=20.0)
        
        d_thick = MaterialManager.MATERIALS["spaghetti"]["thickness"]
        self.sliders.append(Slider("Spagetti Átmérő", "m", d_thick/20.0, d_thick*20.0, MaterialManager.MATERIALS["spaghetti"], "thickness", is_log=True))

        # --- GLOBALS ---
        self.temp_slider = Slider("Alap Hőm.", "°C", 0.0, 50.0, MaterialManager.SETTINGS, "base_temp")
        self.sliders.append(self.temp_slider)

        d_mass = MaterialManager.AGENT["mass"]
        self.sliders.append(Slider("Ixchel Tömege", "kg", d_mass/20.0, d_mass*20.0, MaterialManager.AGENT, "mass", is_log=True)) 
        self.sliders.append(Slider("Ixchel Sebessége", "m/s", 1.0, 20.0, MaterialManager.AGENT, "speed"))

        # --- LAYOUT ---
        current_y = self.scroll_area_top + self.content_padding_top
        self.slider_gap = 42
        sliders_h = len(self.sliders) * self.slider_gap
        
        button_start_y = current_y + sliders_h + 10
        btn_w = 240
        btn_h = 35
        
        r1 = pygame.Rect(self.x + 30, button_start_y, btn_w, btn_h)
        self.scrollable_buttons.append(Button("Nézet Váltása (V)", r1, self.toggle_view_mode))
        
        r2 = pygame.Rect(self.x + 30, button_start_y + 45, btn_w, btn_h)
        self.scrollable_buttons.append(Button("Feliratok Váltása (T)", r2, self.toggle_text_mode))

        # Fixed Buttons
        r_quit = pygame.Rect(self.x + 30, self.h - 70, btn_w, btn_h)
        self.fixed_buttons.append(Button("Kilépés", r_quit, self.trigger_quit))
        
        last_element_bottom = button_start_y + 45 + btn_h + self.content_padding_bottom
        self.content_height = last_element_bottom - self.scroll_area_top

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
            if event.type == pygame.MOUSEWHEEL:
                scroll_speed = 25
                self.scroll_y -= event.y * scroll_speed
                visible_h = self.scroll_area_bottom - self.scroll_area_top
                max_scroll = max(0, self.content_height - visible_h)
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))
                return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.fixed_buttons:
                    if btn.rect.collidepoint(mx, my): btn.callback()
                
                if self.scroll_area_top <= my <= self.scroll_area_bottom:
                    for btn in self.scrollable_buttons:
                         scrolled_rect = btn.rect.move(0, -self.scroll_y)
                         if scrolled_rect.collidepoint(mx, my): btn.callback()
            return True 
        return False

    def update(self):
        if not self.visible: return
        mx, my = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        mouse_in_view = (self.scroll_area_top <= my <= self.scroll_area_bottom) and (mx > self.x)
        start_y = self.scroll_area_top + self.content_padding_top
        
        for i, slider in enumerate(self.sliders):
            slider_y = start_y + i * self.slider_gap - self.scroll_y
            if self.scroll_area_top - 25 < slider_y < self.scroll_area_bottom:
                rect = pygame.Rect(self.x + 30, slider_y, 240, 12)
                slider.update(rect, (mx, my), mouse_down and mouse_in_view)
        
        for btn in self.scrollable_buttons:
             if mouse_in_view: btn.update((mx, my), mouse_down, False, self.scroll_y)
             else: btn.hover = False

        for btn in self.fixed_buttons:
            btn.update((mx, my), mouse_down, False, 0)

    def draw(self, surface):
        if not self.visible: return
        
        s = pygame.Surface((self.w, self.h))
        s.set_alpha(245)
        s.fill((35, 40, 35))
        surface.blit(s, (self.x, self.y))
        
        pygame.draw.line(surface, COLOR_UI_BORDER, (self.x, 0), (self.x, self.h), 3)
        font = pygame.font.SysFont("arial", 20, bold=True)
        h = font.render("Tulajdonságok", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(h, (self.x + 30, 20))
        pygame.draw.line(surface, (60, 60, 60), (self.x + 20, 50), (self.x + self.w - 20, 50), 1)
        
        clip_rect = pygame.Rect(self.x, self.scroll_area_top, self.w, self.scroll_area_bottom - self.scroll_area_top)
        surface.set_clip(clip_rect)
        
        start_y = self.scroll_area_top + self.content_padding_top
        for i, slider in enumerate(self.sliders):
            slider_y = start_y + i * self.slider_gap - self.scroll_y
            if slider_y > self.scroll_area_top - 40 and slider_y < self.scroll_area_bottom + 20:
                rect = pygame.Rect(self.x + 30, slider_y, 240, 12)
                slider.draw(surface, rect)
            
        for btn in self.scrollable_buttons:
            btn_scrolled_y = btn.rect.y - self.scroll_y
            if btn_scrolled_y > self.scroll_area_top - 40 and btn_scrolled_y < self.scroll_area_bottom:
                btn.draw(surface, self.scroll_y)
        
        if self.scrollable_buttons:
            last_btn = self.scrollable_buttons[-1]
            last_y = last_btn.rect.bottom - self.scroll_y
            if last_y < self.scroll_area_bottom:
                info_font = pygame.font.SysFont("arial", 12)
                v_modes = ["Erők (Kék/Piros)", "Anyagminta (Normál)", "Terhelés (Gradiens)"]
                v_str = f"Nézet: {v_modes[self.view_mode]}"
                v_txt = info_font.render(v_str, True, (180, 200, 180))
                surface.blit(v_txt, (self.x + 30, last_y + 10))

                t_modes = ["Pontos Érték", "% Terhelés", "Nincs"]
                t_str = f"Adat: {t_modes[self.text_mode]}"
                t_txt = info_font.render(t_str, True, (180, 200, 180))
                surface.blit(t_txt, (self.x + 30, last_y + 25))
        
        surface.set_clip(None)
        for btn in self.fixed_buttons: btn.draw(surface, 0)