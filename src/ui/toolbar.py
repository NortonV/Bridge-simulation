import pygame
from core.constants import *
from entities.beam import BeamType

class Toolbar:
    def __init__(self, width, height):
        self.screen_w = width
        self.screen_h = height
        
        self.tools = [
            {"name": "Fa gerenda", "key": "1", "type": BeamType.WOOD, "color": COLOR_WOOD},
            {"name": "Bambusz", "key": "2", "type": BeamType.BAMBOO, "color": COLOR_BAMBOO},
            {"name": "Acél", "key": "3", "type": BeamType.STEEL, "color": COLOR_STEEL},
            {"name": "Spagetti", "key": "4", "type": BeamType.SPAGHETTI, "color": COLOR_SPAGHETTI},
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
            if event.key == pygame.K_4: self.active_index = 3
            if event.key == pygame.K_x: self.active_index = 4
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            # Check clicks (Bottom of screen)
            # New height 75 + margin 15 = 90
            y_start = self.screen_h - 90
            if my > y_start:
                icon_w = 90 # Increased from 60
                total_w = len(self.tools) * icon_w
                start_x = (self.screen_w - total_w) // 2
                
                if start_x <= mx <= start_x + total_w:
                    idx = (mx - start_x) // icon_w
                    if 0 <= idx < len(self.tools):
                        self.active_index = int(idx)

    def draw(self, surface):
        # Increased dimensions by 50% (was 60x50)
        icon_w = 90
        icon_h = 75
        y = self.screen_h - 90
        
        total_w = len(self.tools) * icon_w
        start_x = (self.screen_w - total_w) // 2
        
        # Background
        bg_rect = pygame.Rect(start_x - 10, y - 5, total_w + 20, icon_h + 10)
        pygame.draw.rect(surface, (30, 35, 40), bg_rect, border_radius=10)
        pygame.draw.rect(surface, (60, 70, 80), bg_rect, 2, border_radius=10)
        
        # Increased font size for readability
        font = pygame.font.SysFont("arial", 14, bold=True)
        key_font = pygame.font.SysFont("arial", 12)

        for i, tool in enumerate(self.tools):
            x = start_x + i * icon_w
            rect = pygame.Rect(x + 5, y + 5, icon_w - 10, icon_h - 10)
            
            # Highlight selected
            if i == self.active_index:
                pygame.draw.rect(surface, (60, 70, 80), rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_TEXT_HIGHLIGHT, rect, 2, border_radius=6)
            else:
                pygame.draw.rect(surface, (40, 45, 50), rect, border_radius=6)
            
            # Color indicator
            color = tool["color"]
            pygame.draw.circle(surface, color, (rect.centerx, rect.centery - 10), 10)
            
            # Label - Full name (removed slice [:3])
            lbl = font.render(tool["name"], True, (200, 200, 200))
            surface.blit(lbl, (rect.centerx - lbl.get_width()//2, rect.centery + 10))
            
            # Key hint
            k_txt = key_font.render(tool["key"], True, (150, 150, 150))
            surface.blit(k_txt, (rect.right - 12, rect.top + 4))