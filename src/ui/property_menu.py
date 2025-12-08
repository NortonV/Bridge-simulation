import pygame
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
        color = (80, 80, 100) if self.hover else (60, 60, 70)
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 1, border_radius=5)
        
        font = pygame.font.SysFont("arial", 12)
        txt = font.render(self.label, True, (255, 255, 255))
        tx = self.rect.centerx - txt.get_width() // 2
        ty = self.rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))

class Slider:
    def __init__(self, label, key, min_v, max_v, parent_dict, dict_key):
        self.label = label
        self.key = key 
        self.min_v = min_v
        self.max_v = max_v
        self.parent_dict = parent_dict 
        self.dict_key = dict_key       
        self.dragging = False

    def update(self, rect, mouse_pos, mouse_down):
        mx, my = mouse_pos
        curr = self.parent_dict[self.dict_key]
        
        if mouse_down:
            if rect.collidepoint(mx, my):
                self.dragging = True
        else:
            self.dragging = False
            
        if self.dragging:
            ratio = (mx - rect.x) / rect.width
            ratio = max(0.0, min(1.0, ratio))
            new_val = self.min_v + ratio * (self.max_v - self.min_v)
            self.parent_dict[self.dict_key] = new_val

    def draw(self, surface, rect):
        curr = self.parent_dict[self.dict_key]
        
        pygame.draw.rect(surface, (50, 50, 50), rect)
        
        ratio = (curr - self.min_v) / (self.max_v - self.min_v)
        fill_w = int(rect.width * ratio)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, (100, 200, 255), fill_rect)
        
        pygame.draw.rect(surface, (150, 150, 150), rect, 1)
        
        font = pygame.font.SysFont("arial", 12)
        txt = font.render(f"{self.label}: {curr:.3f}", True, (255, 255, 255))
        surface.blit(txt, (rect.x, rect.y - 15))

class PropertyMenu:
    def __init__(self, screen_w, screen_h):
        self.w = 260
        self.h = screen_h
        self.x = screen_w - self.w
        self.y = 0
        self.visible = False
        
        self.sliders = []
        self.buttons = []
        
        self.view_mode = 1 # 0=Stress, 1=Texture, 2=Gradient
        self.text_mode = 0 # 0=Value, 1=Percent, 2=None
        
        self.setup_ui()

    def setup_ui(self):
        # --- Sliders ---
        # Wood
        self.sliders.append(Slider("Wood Stiffness", "E", 100, 5000, MaterialManager.MATERIALS["wood"], "E"))
        self.sliders.append(Slider("Wood Density", "density", 0.1, 5.0, MaterialManager.MATERIALS["wood"], "density"))
        self.sliders.append(Slider("Wood Strength", "strength", 0.001, 0.2, MaterialManager.MATERIALS["wood"], "strength"))
        self.sliders.append(Slider("Wood Thickness", "thickness", 0.01, 0.5, MaterialManager.MATERIALS["wood"], "thickness"))
        
        # Bamboo
        self.sliders.append(Slider("Bamboo Stiffness", "E", 100, 5000, MaterialManager.MATERIALS["bamboo"], "E"))
        self.sliders.append(Slider("Bamboo Density", "density", 0.1, 5.0, MaterialManager.MATERIALS["bamboo"], "density"))
        self.sliders.append(Slider("Bamboo Strength", "strength", 0.001, 0.5, MaterialManager.MATERIALS["bamboo"], "strength"))
        self.sliders.append(Slider("Bamboo Thickness", "thickness", 0.01, 0.5, MaterialManager.MATERIALS["bamboo"], "thickness"))

        # Vine
        self.sliders.append(Slider("Vine Stiffness", "E", 10, 500, MaterialManager.MATERIALS["vine"], "E"))
        self.sliders.append(Slider("Vine Density", "density", 0.1, 5.0, MaterialManager.MATERIALS["vine"], "density"))
        self.sliders.append(Slider("Vine Strength", "strength", 0.01, 1.0, MaterialManager.MATERIALS["vine"], "strength"))
        self.sliders.append(Slider("Vine Thickness", "thickness", 0.01, 0.3, MaterialManager.MATERIALS["vine"], "thickness"))

        # Agent
        self.sliders.append(Slider("Agent Mass", "mass", 1.0, 500.0, MaterialManager.AGENT, "mass"))
        self.sliders.append(Slider("Agent Speed", "speed", 1.0, 20.0, MaterialManager.AGENT, "speed"))

        # --- Buttons ---
        start_y = 50 + len(self.sliders) * 40 + 20
        btn_w = 200
        btn_h = 30
        
        r1 = pygame.Rect(self.x + 20, start_y, btn_w, btn_h)
        self.buttons.append(Button("Toggle Visual Mode", r1, self.toggle_view_mode))
        
        r2 = pygame.Rect(self.x + 20, start_y + 40, btn_w, btn_h)
        self.buttons.append(Button("Toggle Text Overlay", r2, self.toggle_text_mode))

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
        
        start_y = 50
        gap = 40
        
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 20, start_y + i*gap, 200, 15)
            slider.update(rect, (mx, my), mouse_down)
            
        for btn in self.buttons:
            btn.update((mx, my), mouse_down, False)

    def draw(self, surface):
        if not self.visible: return
        
        s = pygame.Surface((self.w, self.h))
        s.set_alpha(230)
        s.fill((20, 20, 30))
        surface.blit(s, (self.x, self.y))
        pygame.draw.line(surface, (100, 100, 100), (self.x, 0), (self.x, self.h), 2)
        
        font = pygame.font.SysFont("arial", 16, bold=True)
        h = font.render("Material Properties", True, (255, 255, 255))
        surface.blit(h, (self.x + 20, 15))
        
        start_y = 50
        gap = 40
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 20, start_y + i*gap, 200, 15)
            slider.draw(surface, rect)
            
        for btn in self.buttons:
            btn.draw(surface)
            
        info_font = pygame.font.SysFont("arial", 12)
        v_modes = ["Stress (Red/Blue)", "Texture (Normal)", "Gradient (Load)"]
        v_str = f"Visual: {v_modes[self.view_mode]}"
        v_txt = info_font.render(v_str, True, (200, 200, 200))
        surface.blit(v_txt, (self.x + 20, self.buttons[0].rect.bottom + 5))

        t_modes = ["Exact Value", "% Max Load", "None"]
        t_str = f"Overlay: {t_modes[self.text_mode]}"
        t_txt = info_font.render(t_str, True, (200, 200, 200))
        surface.blit(t_txt, (self.x + 20, self.buttons[1].rect.bottom + 5))
            
        mode = "HOLLOW" if MaterialManager.PLACEMENT_MODE_HOLLOW else "SOLID"
        col = (100, 255, 100) if not MaterialManager.PLACEMENT_MODE_HOLLOW else (100, 200, 255)
        
        txt = info_font.render(f"Placement Mode: {mode}", True, col)
        surface.blit(txt, (self.x + 20, self.h - 60))
        
        txt2 = info_font.render("[J] Solid  |  [H] Hollow", True, (150, 150, 150))
        surface.blit(txt2, (self.x + 20, self.h - 40))