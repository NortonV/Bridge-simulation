import pygame
from core.constants import *

class GraphOverlay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.history = [] 
        self.max_len = width - 4 # Padding
        self.visible = False
        self.eng_max_peak = 100.0

    def toggle(self):
        self.visible = not self.visible
    
    def reset_data(self):
        self.history = []
        self.eng_max_peak = 100.0

    def update(self, value, percent, mode):
        if not self.visible: return
        self.history.append((value, percent, mode))
        if len(self.history) > self.max_len:
            self.history.pop(0)

        if mode == "ANALYSIS":
            if value > self.eng_max_peak: self.eng_max_peak = value
            if percent > self.eng_max_peak: self.eng_max_peak = percent

    def draw(self, surface):
        if not self.visible: return

        # Graph Background
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(220)
        s.fill((20, 25, 20))
        surface.blit(s, self.rect)
        
        # Border
        pygame.draw.rect(surface, COLOR_UI_BORDER, self.rect, 2)
        
        # Grid lines inside graph
        for i in range(1, 4):
            y_pos = self.rect.y + (self.rect.height * i // 4)
            pygame.draw.line(surface, (50, 60, 50), (self.rect.x, y_pos), (self.rect.right, y_pos), 1)

        if not self.history: 
            # "No Data" text
            font = pygame.font.SysFont("arial", 14)
            txt = font.render("Várakozás adatokra...", True, (100, 100, 100))
            surface.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery))
            return

        y_max = self.eng_max_peak
        label_red = "Maximális Erő (N)"
        label_green = "Terhelés (%)"

        points_force = []
        points_load = []
        
        for i, (val, perc, mode) in enumerate(self.history):
            if mode != "ANALYSIS": continue

            px = self.rect.x + 2 + i
            if y_max == 0: norm_f, norm_p = 0, 0
            else: 
                norm_f = min(1.0, val / y_max)
                norm_p = min(1.0, perc / y_max)
            
            # Keep inside padding
            h = self.rect.height - 20
            py_f = (self.rect.bottom - 10) - (norm_f * h)
            py_p = (self.rect.bottom - 10) - (norm_p * h)
            
            points_force.append((px, py_f))
            points_load.append((px, py_p))

        # Use Anti-aliased lines for smoother graphs
        if len(points_force) > 1:
            pygame.draw.aalines(surface, COLOR_TENSION, False, points_force)
        if len(points_load) > 1:
            pygame.draw.aalines(surface, (100, 255, 100), False, points_load)

        # Labels & Values
        font = pygame.font.SysFont("arial", 12, bold=True)
        
        # Max Scale Label
        top_txt = f"{int(y_max)}"
        surface.blit(font.render(top_txt, True, (150, 150, 150)), (self.rect.x + 5, self.rect.y + 5))
        
        # Legend
        surface.blit(font.render(label_red, True, COLOR_TENSION), (self.rect.x + 5, self.rect.bottom - 40))
        surface.blit(font.render(label_green, True, (100, 255, 100)), (self.rect.x + 5, self.rect.bottom - 20))
        
        # Current Real-time Values
        curr_force = self.history[-1][0]
        curr_perc = self.history[-1][1]
        
        surf_f = font.render(f"{int(curr_force)} N", True, COLOR_TENSION)
        surf_p = font.render(f"{int(curr_perc)} %", True, (100, 255, 100))
        
        surface.blit(surf_f, (self.rect.right - 60, self.rect.bottom - 40))
        surface.blit(surf_p, (self.rect.right - 60, self.rect.bottom - 20))