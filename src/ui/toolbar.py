import pygame
from core.constants import *
from entities.beam import BeamType

class Toolbar:
    def __init__(self, width, height):
        self.screen_w = width
        self.screen_h = height
        
        # Tools
        self.tools = [
            {"name": "Bamboo", "key": "1", "type": BeamType.BAMBOO, "color": COLOR_BAMBOO},
            {"name": "Vine", "key": "2", "type": BeamType.VINE, "color": COLOR_VINE},
            {"name": "Wood", "key": "3", "type": BeamType.WOOD, "color": COLOR_WOOD},
            {"name": "Delete", "key": "D", "type": "DELETE", "color": (200, 50, 50)}
        ]
        self.active_index = 0 

    @property
    def selected_tool(self):
        return self.tools[self.active_index]

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: self.active_index = 0
            if event.key == pygame.K_2: self.active_index = 1
            if event.key == pygame.K_3: self.active_index = 2
            if event.key == pygame.K_d: self.active_index = 3

    def draw(self, surface):
        # Draw Panel Background
        panel_h = 60
        y_pos = self.screen_h - panel_h
        s = pygame.Surface((self.screen_w, panel_h))
        s.set_alpha(200)
        s.fill((30, 30, 30))
        surface.blit(s, (0, y_pos))

        # Draw Buttons
        btn_w = 120
        gap = 20
        total_w = len(self.tools) * (btn_w + gap)
        start_x = (self.screen_w - total_w) // 2
        
        font = pygame.font.SysFont("monospace", 16, bold=True)

        for i, tool in enumerate(self.tools):
            bx = start_x + i * (btn_w + gap)
            by = y_pos + 10
            
            is_active = (i == self.active_index)
            border_col = (255, 255, 255) if is_active else (100, 100, 100)
            thickness = 3 if is_active else 1
            
            rect = pygame.Rect(bx, by, btn_w, 40)
            pygame.draw.rect(surface, tool["color"], rect)
            pygame.draw.rect(surface, border_col, rect, thickness)
            
            label = f"{tool['key']}: {tool['name']}"
            txt = font.render(label, True, (255, 255, 255))
            tx = bx + (btn_w - txt.get_width()) // 2
            ty = by + (40 - txt.get_height()) // 2
            surface.blit(txt, (tx, ty))