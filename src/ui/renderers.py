"""
Specialized renderers for analysis mode visualization.
"""
import pygame
import math
from core.constants import *
from core.material_manager import MaterialManager
from utils.math_utils import hermite_spline_point, normalize_angle
from utils.render_utils import (
    draw_curved_beam, draw_node, draw_broken_beam,
    interpolate_color, create_semi_transparent_surface
)


def draw_ixchel(surface, screen_x, screen_y):
    """
    Draw the Ixchel character (simple stick figure).
    
    Args:
        surface: Pygame surface
        screen_x, screen_y: Screen coordinates
    """
    # Body
    pygame.draw.rect(surface, (139, 69, 19),
                     (screen_x - 5, screen_y - 25, 10, 20))
    # Head
    pygame.draw.circle(surface, (210, 180, 140),
                      (screen_x, screen_y - 32), 8)
    # Hat
    pygame.draw.aaline(surface, (100, 70, 40),
                      (screen_x - 12, screen_y - 42),
                      (screen_x + 12, screen_y - 42))


class AnalysisRenderer:
    """
    Renders the deformed structure during analysis mode.
    
    Handles:
    - Deformed beam curves using Hermite splines
    - Color coding based on view mode
    - Stress labels
    - Broken beam visualization
    """
    
    # Number of segments for curved beam rendering
    CURVE_SEGMENTS = 12
    
    def __init__(self, grid, prop_menu):
        self.grid = grid
        self.prop_menu = prop_menu

    def draw(self, surface, bridge, solver, broken_beams, exaggeration):
        """
        Draw the complete deformed structure.
        
        Args:
            surface: Pygame surface
            bridge: Bridge object
            solver: StaticSolver with current results
            broken_beams: Set of beams that have failed
            exaggeration: Displacement exaggeration factor
        """
        if not solver:
            return
        
        # Draw all nodes
        for node in bridge.nodes:
            self._draw_deformed_node(surface, node, solver, exaggeration)
        
        # Draw all beams
        for beam in bridge.beams:
            self._draw_deformed_beam(
                surface, beam, solver, broken_beams, exaggeration
            )

    def _draw_deformed_node(self, surface, node, solver, exaggeration):
        """Draw a single deformed node."""
        dx, dy, _ = solver.displacements.get(node, (0, 0, 0))
        def_x = node.x + dx * exaggeration
        def_y = node.y + dy * exaggeration
        pos = self.grid.world_to_screen(def_x, def_y)
        
        color = (180, 50, 50) if node.fixed else (80, 80, 80)
        pygame.draw.circle(surface, color, pos, 5)

    def _draw_deformed_beam(self, surface, beam, solver, broken_beams, exaggeration):
        """Draw a single deformed beam with appropriate styling."""
        # Get node displacements
        da_x, da_y, da_theta = solver.displacements.get(beam.node_a, (0, 0, 0))
        db_x, db_y, db_theta = solver.displacements.get(beam.node_b, (0, 0, 0))
        
        # Calculate deformed endpoints
        p1_x = beam.node_a.x + da_x * exaggeration
        p1_y = beam.node_a.y + da_y * exaggeration
        p2_x = beam.node_b.x + db_x * exaggeration
        p2_y = beam.node_b.y + db_y * exaggeration
        
        # Calculate curve parameters
        chord_dx = p2_x - p1_x
        chord_dy = p2_y - p1_y
        length = math.hypot(chord_dx, chord_dy)
        psi = math.atan2(chord_dy, chord_dx)
        
        # Original beam angle
        orig_dx = beam.node_b.x - beam.node_a.x
        orig_dy = beam.node_b.y - beam.node_a.y
        alpha = math.atan2(orig_dy, orig_dx)
        
        # Rotations relative to deformed chord
        rot1 = normalize_angle((alpha + da_theta * exaggeration) - psi)
        rot2 = normalize_angle((alpha + db_theta * exaggeration) - psi)
        
        # Generate curve points
        points = self._generate_curve_points(
            (p1_x, p1_y), (p2_x, p2_y), rot1, rot2, length
        )
        
        # Determine visual properties
        props = MaterialManager.get_properties(beam.type, beam.hollow_ratio)
        width = max(2, int(props['thickness'] * PPM))
        color = self._get_beam_color(beam, solver)
        
        # Draw beam
        if beam in broken_beams:
            draw_broken_beam(surface, points, width)
        else:
            draw_curved_beam(surface, points, color, width,
                           beam.type, beam.hollow_ratio)
        
        # Draw stress label
        if self.prop_menu.text_mode != 2:
            self._draw_stress_label(surface, beam, solver, points, color)

    def _generate_curve_points(self, p1, p2, rot1, rot2, length):
        """Generate screen points along the deformed beam curve."""
        points = []
        
        for i in range(self.CURVE_SEGMENTS + 1):
            t = i / self.CURVE_SEGMENTS
            wx, wy = hermite_spline_point(t, p1, p2, rot1, rot2, length)
            screen_pos = self.grid.world_to_screen(wx, wy)
            points.append(screen_pos)
        
        return points

    def _get_beam_color(self, beam, solver):
        """
        Determine beam color based on current view mode.
        
        View modes:
        0 - Force (blue=compression, red=tension)
        1 - Material (original beam color)
        2 - Stress (gradient from material color to red)
        """
        view_mode = self.prop_menu.view_mode
        
        if view_mode == 0:
            # Force view
            force = solver.results.get(beam, 0)
            return COLOR_COMPRESSION if force < 0 else COLOR_TENSION
        
        elif view_mode == 1:
            # Material view
            return beam.color
        
        elif view_mode == 2:
            # Stress gradient view
            ratio = solver.stress_ratios.get(beam, 0.0)
            ratio = min(1.0, ratio)  # Clamp to 1.0
            return interpolate_color(beam.color, (255, 50, 50), ratio)
        
        return (100, 100, 100)  # Fallback

    def _draw_stress_label(self, surface, beam, solver, points, color):
        """Draw stress value label at beam midpoint."""
        if not points:
            return
        
        # Get label text
        text_mode = self.prop_menu.text_mode
        if text_mode == 0:
            # Show force values
            axial = int(abs(solver.results.get(beam, 0)))
            bending = int(abs(solver.bending_results.get(beam, 0)))
            label = f"{axial}N | {bending}N"
        elif text_mode == 1:
            # Show percentage
            ratio = solver.stress_ratios.get(beam, 0)
            label = f"{int(ratio * 100)}%"
        else:
            return
        
        # Draw at midpoint
        mid_idx = len(points) // 2
        mx, my = points[mid_idx]
        
        from utils.render_utils import draw_text_with_background
        font = pygame.font.SysFont("arial", 16, bold=True)
        draw_text_with_background(
            surface, label, font, (mx, my),
            (255, 255, 255), (20, 20, 20), color
        )


class VolumePopup:
    """
    Renders the volume adjustment popup in the bottom-right corner.
    """
    
    WIDTH = 220
    HEIGHT = 60
    MARGIN = 30
    
    def draw(self, surface, volume, timer):
        """
        Draw volume popup if timer is active.
        
        Args:
            surface: Pygame surface
            volume: Current volume (0.0 to 1.0)
            timer: Frames remaining to display
        """
        if timer <= 0:
            return
        
        # Calculate position
        w, h = surface.get_size()
        x = w - self.WIDTH - self.MARGIN
        y = h - self.HEIGHT - self.MARGIN
        
        # Calculate alpha (fade out in last 20 frames)
        alpha = 230
        if timer < 20:
            alpha = int(230 * (timer / 20))
        
        # Create semi-transparent surface
        popup = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        
        # Background
        pygame.draw.rect(popup, (30, 35, 30, alpha),
                        (0, 0, self.WIDTH, self.HEIGHT), border_radius=10)
        pygame.draw.rect(popup, (*COLOR_UI_BORDER, alpha),
                        (0, 0, self.WIDTH, self.HEIGHT), 2, border_radius=10)
        
        # Volume bar
        bar_w, bar_h = 180, 8
        bx = (self.WIDTH - bar_w) // 2
        by = 35
        
        # Bar background
        pygame.draw.rect(popup, (50, 60, 50, alpha),
                        (bx, by, bar_w, bar_h), border_radius=4)
        
        # Bar fill
        fill_w = int(bar_w * volume)
        if fill_w > 0:
            pygame.draw.rect(popup, (100, 200, 255, alpha),
                           (bx, by, fill_w, bar_h), border_radius=4)
        
        # Text
        font = pygame.font.SysFont("arial", 16, bold=True)
        text = font.render(f"HangerÅ': {int(volume * 100)}%", True, COLOR_TEXT_MAIN)
        text.set_alpha(alpha)
        popup.blit(text, (self.WIDTH // 2 - text.get_width() // 2, 10))
        
        surface.blit(popup, (x, y))