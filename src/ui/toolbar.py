import pygame
from core.constants import *
from entities.beam import BeamType

class Toolbar:
    def __init__(self, width, height):
        self.screen_w = width
        self.screen_h = height
        
        # Tools translated to Hungarian
        self.tools = [
            {"name": "Fa gerenda", "key": "1", "type": BeamType.WOOD, "color": COLOR_WOOD},
            {"name": "Bambusz", "key": "2", "type": BeamType.BAMBOO, "color": COLOR_BAMBOO},
            {"name": "Inda kötél", "key": "3", "type": BeamType.VINE, "color": COLOR_VINE},
            {"name": "Törlés", "key": "X", "type": "DELETE", "color": (200, 60, 60)}
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
            if event.key == pygame.K_x: self.active_index = 3

    def draw(self, surface):
        # Draw Panel Background (Stone/Jungle UI style)
        panel_h = 80
        y_pos = self.screen_h - panel_h
        
        # Main background
        s = pygame.Surface((self.screen_w, panel_h))
        s.set_alpha(240)
        s.fill((30, 35, 30)) # Dark Jungle Green
        surface.blit(s, (0, y_pos))
        
        # Gold Border top
        pygame.draw.line(surface, COLOR_UI_BORDER, (0, y_pos), (self.screen_w, y_pos), 3)

        # Draw Buttons
        btn_w = 160
        btn_h = 50
        gap = 20
        total_w = len(self.tools) * (btn_w + gap)
        start_x = (self.screen_w - total_w) // 2
        
        font = pygame.font.SysFont("arial", 14, bold=True)
        key_font = pygame.font.SysFont("arial", 12)

        for i, tool in enumerate(self.tools):
            bx = start_x + i * (btn_w + gap)
            by = y_pos + 15
            
            is_active = (i == self.active_index)
            
            # Button Background
            bg_col = (60, 70, 60) if not is_active else (80, 90, 80)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            pygame.draw.rect(surface, bg_col, rect, border_radius=8)
            
            # Border (Gold if active)
            border_col = COLOR_UI_BORDER if is_active else (100, 100, 100)
            thickness = 3 if is_active else 1
            pygame.draw.rect(surface, border_col, rect, thickness, border_radius=8)
            
            # Material Icon (Left side of button)
            icon_rect = pygame.Rect(bx + 10, by + 10, 30, 30)
            if tool["type"] == "DELETE":
                # Draw an X
                pygame.draw.line(surface, tool["color"], (bx+15, by+15), (bx+35, by+35), 3)
                pygame.draw.line(surface, tool["color"], (bx+35, by+15), (bx+15, by+35), 3)
            else:
                pygame.draw.rect(surface, tool["color"], icon_rect, border_radius=4)
            
            # Text Labels
            name_txt = font.render(tool['name'], True, COLOR_TEXT_MAIN)
            surface.blit(name_txt, (bx + 50, by + 10))
            
            key_txt = key_font.render(f"Gomb: [{tool['key']}]", True, (180, 180, 180))
            surface.blit(key_txt, (bx + 50, by + 30))
            
            # Active Indicator Triangle
            if is_active:
                mid_x = bx + btn_w // 2
                pts = [(mid_x, y_pos), (mid_x - 6, y_pos - 6), (mid_x + 6, y_pos - 6)]
                pygame.draw.polygon(surface, COLOR_UI_BORDER, pts)