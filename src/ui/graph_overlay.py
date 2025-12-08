import pygame

class GraphOverlay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        # Stores (value, percent, mode) tuples
        self.history = [] 
        self.max_len = width # 1 pixel per data point
        self.visible = False
        
        # Scaling State
        self.eng_max_peak = 100.0 # Starts at 100N, grows if forces get higher

    def toggle(self):
        self.visible = not self.visible
    
    def reset_data(self):
        self.history = []
        self.eng_max_peak = 100.0

    def update(self, value, percent, mode):
        if not self.visible: return

        # Update History
        self.history.append((value, percent, mode))
        if len(self.history) > self.max_len:
            self.history.pop(0)

        # Update Engineering Peak (Auto-Scaling Y-Axis)
        if mode == "ANALYSIS":
            if value > self.eng_max_peak:
                self.eng_max_peak = value
            # Ensure graph fits percentage too
            if percent > self.eng_max_peak:
                self.eng_max_peak = percent

    def draw(self, surface):
        if not self.visible: return

        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(200)
        s.fill((20, 20, 20))
        surface.blit(s, self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        if not self.history: return

        y_max = self.eng_max_peak
        label_red = "Force (N)"
        label_green = "Load (%)"

        points_force = []
        points_load = []
        
        for i, (val, perc, mode) in enumerate(self.history):
            if mode != "ANALYSIS": continue

            px = self.rect.x + i
            
            if y_max == 0: 
                norm_f = 0
                norm_p = 0
            else: 
                norm_f = min(1.5, val / y_max)
                norm_p = min(1.5, perc / y_max)
            
            py_f = self.rect.bottom - (norm_f * self.rect.height)
            py_p = self.rect.bottom - (norm_p * self.rect.height)
            
            points_force.append((px, py_f))
            points_load.append((px, py_p))

        if len(points_force) > 1:
            pygame.draw.lines(surface, (255, 80, 80), False, points_force, 2)
        if len(points_load) > 1:
            pygame.draw.lines(surface, (80, 255, 80), False, points_load, 2)

        font = pygame.font.SysFont("arial", 12)
        
        top_txt = f"{int(y_max)}"
        surface.blit(font.render(top_txt, True, (150, 150, 150)), (self.rect.x + 5, self.rect.y + 5))
        
        surface.blit(font.render(label_red, True, (255, 80, 80)), (self.rect.x + 5, self.rect.bottom - 35))
        surface.blit(font.render(label_green, True, (80, 255, 80)), (self.rect.x + 5, self.rect.bottom - 20))
        
        curr_force = self.history[-1][0]
        curr_perc = self.history[-1][1]
        
        surf_f = font.render(f"{int(curr_force)}N", True, (255, 80, 80))
        surf_p = font.render(f"{int(curr_perc)}%", True, (80, 255, 80))
        
        surface.blit(surf_f, (self.rect.right - 50, self.rect.bottom - 35))
        surface.blit(surf_p, (self.rect.right - 50, self.rect.bottom - 20))