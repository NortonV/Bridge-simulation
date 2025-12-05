import pygame
import math
from .constants import *

class Grid:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        
        # Center the Origin (0,0) horizontally
        self.offset_x = screen_width // 2
        
        # Place Origin 100 pixels from the bottom of the screen
        self.offset_y = screen_height - 100

    def world_to_screen(self, world_x, world_y):
        """Converts Physics Meters -> Screen Pixels"""
        screen_x = int(self.offset_x + (world_x * PPM))
        screen_y = int(self.offset_y - (world_y * PPM)) # Flip Y axis because Pygame Y is down
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Converts Screen Pixels -> Physics Meters"""
        world_x = (screen_x - self.offset_x) / PPM
        world_y = (self.offset_y - screen_y) / PPM      # Flip Y back
        return world_x, world_y

    def snap(self, screen_x, screen_y):
        """
        Takes mouse pixel coordinates and snaps them to the nearest 0.5 meter.
        Returns: (world_x, world_y) in meters.
        """
        raw_wx, raw_wy = self.screen_to_world(screen_x, screen_y)
        
        # Snap to nearest 0.5m step
        step = 0.5
        snapped_x = round(raw_wx / step) * step
        snapped_y = round(raw_wy / step) * step
        
        return snapped_x, snapped_y

    def draw(self, surface):
        """Draws the engineering paper background"""
        surface.fill(COLOR_BG)

        # 1. Determine Visible Range (Optimization)
        # We calculate exactly how many meters fit on the current screen
        min_wx, _ = self.screen_to_world(0, 0)
        max_wx, _ = self.screen_to_world(self.width, self.height)
        
        _, max_wy = self.screen_to_world(0, 0) # Top of screen is high Y
        _, min_wy = self.screen_to_world(0, self.height) # Bottom is low Y

        start_x = int(min_wx) - 1
        end_x = int(max_wx) + 1
        start_y = int(min_wy) - 1
        end_y = int(max_wy) + 1

        # 2. Draw Vertical Lines
        for i in range(start_x, end_x):
            px, _ = self.world_to_screen(i, 0)
            # Major line every 5 meters, minor every 1 meter
            color = COLOR_GRID_MAJOR if i % 5 == 0 else COLOR_GRID_MINOR
            pygame.draw.line(surface, color, (px, 0), (px, self.height))

        # 3. Draw Horizontal Lines
        for i in range(start_y, end_y):
            _, py = self.world_to_screen(0, i)
            color = COLOR_GRID_MAJOR if i % 5 == 0 else COLOR_GRID_MINOR
            pygame.draw.line(surface, color, (0, py), (self.width, py))

        # 4. Draw Main Axes (X=0, Y=0)
        origin_x, origin_y = self.world_to_screen(0, 0)
        
        # Y-Axis (Green Vertical)
        pygame.draw.line(surface, COLOR_AXIS, (origin_x, 0), (origin_x, self.height), 3)
        # X-Axis (Green Horizontal)
        pygame.draw.line(surface, COLOR_AXIS, (0, origin_y), (self.width, origin_y), 3)
        
        # Origin Marker
        pygame.draw.circle(surface, COLOR_AXIS, (origin_x, origin_y), 6)