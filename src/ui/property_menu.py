import pygame
from core.material_manager import MaterialManager

class Slider:
    def __init__(self, label, key, min_v, max_v, parent_dict, dict_key):
        self.label = label
        self.key = key # e.g. "E"
        self.min_v = min_v
        self.max_v = max_v
        self.parent_dict = parent_dict # Reference to dictionary to update
        self.dict_key = dict_key       # Key in that dictionary
        self.dragging = False

    def update(self, rect, mouse_pos, mouse_down):
        mx, my = mouse_pos
        
        # Current Value
        curr = self.parent_dict[self.dict_key]
        
        # Handle Input
        if mouse_down:
            if rect.collidepoint(mx, my):
                self.dragging = True
        else:
            self.dragging = False
            
        if self.dragging:
            # Map Mouse X to Value
            ratio = (mx - rect.x) / rect.width
            ratio = max(0.0, min(1.0, ratio))
            new_val = self.min_v + ratio * (self.max_v - self.min_v)
            self.parent_dict[self.dict_key] = new_val

    def draw(self, surface, rect):
        curr = self.parent_dict[self.dict_key]
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50), rect)
        
        # Fill Bar
        ratio = (curr - self.min_v) / (self.max_v - self.min_v)
        fill_w = int(rect.width * ratio)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surface, (100, 200, 255), fill_rect)
        
        # Outline
        pygame.draw.rect(surface, (150, 150, 150), rect, 1)
        
        # Text
        font = pygame.font.SysFont("arial", 12)
        txt = font.render(f"{self.label}: {curr:.2f}", True, (255, 255, 255))
        surface.blit(txt, (rect.x, rect.y - 15))

class PropertyMenu:
    def __init__(self, screen_w, screen_h):
        self.w = 250
        self.h = screen_h
        self.x = screen_w - self.w
        self.y = 0
        self.visible = False
        
        self.sliders = []
        self.setup_sliders()

    def setup_sliders(self):
        # Wood
        self.sliders.append(Slider("Wood Stiffness", "E", 100, 5000, MaterialManager.MATERIALS["wood"], "E"))
        self.sliders.append(Slider("Wood Density", "density", 0.1, 5.0, MaterialManager.MATERIALS["wood"], "density"))
        
        # Bamboo
        self.sliders.append(Slider("Bamboo Stiffness", "E", 100, 5000, MaterialManager.MATERIALS["bamboo"], "E"))
        self.sliders.append(Slider("Bamboo Density", "density", 0.1, 5.0, MaterialManager.MATERIALS["bamboo"], "density"))
        
        # Vine
        self.sliders.append(Slider("Vine Stiffness", "E", 10, 500, MaterialManager.MATERIALS["vine"], "E"))
        self.sliders.append(Slider("Vine Strength", "strength", 0.01, 1.0, MaterialManager.MATERIALS["vine"], "strength"))
        
        # Agent
        self.sliders.append(Slider("Agent Mass", "mass", 1.0, 50.0, MaterialManager.AGENT, "mass"))

    def toggle(self):
        self.visible = not self.visible

    def handle_input(self, event):
        if not self.visible: return False
        
        mx, my = pygame.mouse.get_pos()
        # mouse_down = pygame.mouse.get_pressed()[0] # Unused here, handled in update
        
        # Block clicks if mouse is over menu
        if mx > self.x:
            return True # Consume event
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

    def draw(self, surface):
        if not self.visible: return
        
        # Background
        s = pygame.Surface((self.w, self.h))
        s.set_alpha(230)
        s.fill((20, 20, 30))
        surface.blit(s, (self.x, self.y))
        pygame.draw.line(surface, (100, 100, 100), (self.x, 0), (self.x, self.h), 2)
        
        # Header
        font = pygame.font.SysFont("arial", 16, bold=True)
        h = font.render("Material Properties", True, (255, 255, 255))
        surface.blit(h, (self.x + 20, 15))
        
        # Sliders
        start_y = 50
        gap = 40
        for i, slider in enumerate(self.sliders):
            rect = pygame.Rect(self.x + 20, start_y + i*gap, 200, 15)
            slider.draw(surface, rect)
            
        # Helper Text
        info_font = pygame.font.SysFont("arial", 12)
        mode = "HOLLOW" if MaterialManager.PLACEMENT_MODE_HOLLOW else "SOLID"
        col = (100, 255, 100) if not MaterialManager.PLACEMENT_MODE_HOLLOW else (100, 200, 255)
        
        txt = info_font.render(f"Placement Mode: {mode}", True, col)
        surface.blit(txt, (self.x + 20, self.h - 60))
        
        txt2 = info_font.render("[J] Solid  |  [H] Hollow", True, (150, 150, 150))
        surface.blit(txt2, (self.x + 20, self.h - 40))