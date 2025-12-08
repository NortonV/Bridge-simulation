import pygame

class GraphOverlay:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.history = [] # Stores (value, mode) tuples
        self.max_len = width # 1 pixel per data point
        self.visible = False
        
        # Scaling State
        self.eng_max_peak = 100.0 # Starts at 100N, grows if forces get higher

    def toggle(self):
        self.visible = not self.visible
    
    def reset_data(self):
        self.history = []
        self.eng_max_peak = 100.0

    def update(self, value, mode):
        if not self.visible: return

        # Update History
        self.history.append((value, mode))
        if len(self.history) > self.max_len:
            self.history.pop(0)

        # Update Engineering Peak (Auto-Scaling Y-Axis)
        if mode == "ANALYSIS":
            if value > self.eng_max_peak:
                self.eng_max_peak = value

    def draw(self, surface):
        if not self.visible: return

        # 1. Draw Background / Frame
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(200) # Semi-transparent black
        s.fill((20, 20, 20))
        surface.blit(s, self.rect)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2)

        if not self.history: 
            return

        # 2. Determine Scale based on current mode
        y_max = self.eng_max_peak
        label = "Max Internal Force"
        unit = "N"
        color = (255, 100, 100) # Red for Engineering

        # 3. Draw Plot Lines
        points = []
        for i, (val, mode) in enumerate(self.history):
            # Only draw points if mode is ANALYSIS
            if mode != "ANALYSIS": continue

            px = self.rect.x + i
            # Normalize height: (val / y_max)
            # Clamp to 0.0 - 1.0 safety
            if y_max == 0: norm = 0
            else: norm = min(1.5, val / y_max) # Allow slight overflow before clipping
            
            py = self.rect.bottom - (norm * self.rect.height)
            points.append((px, py))

        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, 2)

        # 4. Draw UI Labels
        font = pygame.font.SysFont("arial", 12)
        
        # Top Label (Max Y)
        top_txt = f"{int(y_max)} {unit}"
        
        # Current Value Label
        current_val = self.history[-1][0]
        curr_txt = f"{int(current_val)} {unit}"

        # Render Text
        surface.blit(font.render(top_txt, True, (150, 150, 150)), (self.rect.x + 5, self.rect.y + 5))
        surface.blit(font.render(label, True, color), (self.rect.x + 5, self.rect.bottom - 20))
        
        # Value at cursor
        val_surf = font.render(curr_txt, True, (255, 255, 255))
        surface.blit(val_surf, (self.rect.right - 50, self.rect.bottom - 35))