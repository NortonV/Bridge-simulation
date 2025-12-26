"""
Rendering utility functions for beams and UI elements.
"""
import pygame
import math
from entities.beam import BeamType
from core.constants import PPM


def draw_beam_texture(surface, start, end, beam_type, width, color, hollow_ratio):
    """
    Draw a beam with material-specific texturing.
    
    Args:
        surface: Pygame surface to draw on
        start, end: Screen coordinates (x, y)
        beam_type: BeamType enum value
        width: Line width in pixels
        color: Base RGB color
        hollow_ratio: 0.0 to 1.0, determines hollow core visibility
    """
    # Subtle shadow for depth
    shadow_offset = 2
    pygame.draw.line(
        surface, (10, 15, 10),
        (start[0] + shadow_offset, start[1] + shadow_offset),
        (end[0] + shadow_offset, end[1] + shadow_offset),
        width
    )
    
    # Main beam body
    pygame.draw.line(surface, color, start, end, width)
    
    # Material-specific details
    if beam_type == BeamType.BAMBOO:
        _draw_bamboo_segments(surface, start, end, width)
    elif beam_type == BeamType.WOOD:
        _draw_wood_grain(surface, start, end)
    elif beam_type == BeamType.STEEL:
        _draw_steel_shine(surface, start, end)
    elif beam_type == BeamType.SPAGHETTI:
        _draw_spaghetti_strands(surface, start, end, width)
    
    # Hollow core (if applicable)
    if hollow_ratio > 0.0:
        _draw_hollow_core(surface, start, end, width, hollow_ratio)


def _draw_bamboo_segments(surface, start, end, width):
    """Draw bamboo node rings at intervals."""
    for t in [0.25, 0.5, 0.75]:
        tx = start[0] + (end[0] - start[0]) * t
        ty = start[1] + (end[1] - start[1]) * t
        # Dark ring
        pygame.draw.circle(surface, (50, 60, 40), (int(tx), int(ty)), width // 2 + 1)
        # Light center
        pygame.draw.circle(surface, (150, 180, 100), (int(tx), int(ty)), width // 2 - 1)


def _draw_wood_grain(surface, start, end):
    """Draw subtle wood grain line."""
    pygame.draw.line(surface, (80, 40, 10), start, end, 1)


def _draw_steel_shine(surface, start, end):
    """Draw metallic highlight."""
    pygame.draw.line(surface, (150, 160, 170), start, end, 2)


def _draw_spaghetti_strands(surface, start, end, width):
    """Draw multiple thin parallel strands."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    
    if length > 0:
        # Perpendicular offset direction
        nx = -dy / length
        ny = dx / length
        
        # Draw 3 parallel strands
        for offset in [-1.5, 0, 1.5]:
            ox, oy = nx * offset, ny * offset
            s_off = (start[0] + ox, start[1] + oy)
            e_off = (end[0] + ox, end[1] + oy)
            pygame.draw.line(surface, (255, 255, 150), s_off, e_off, 1)


def _draw_hollow_core(surface, start, end, width, hollow_ratio):
    """Draw white hollow core in center of beam."""
    border_thickness = max(2, int(width * 0.15))
    inner_width = max(0, width - (border_thickness * 2))
    
    if inner_width > 0:
        pygame.draw.line(surface, (255, 255, 255), start, end, inner_width)


def draw_curved_beam(surface, points, color, width, beam_type, hollow_ratio):
    """
    Draw a curved beam using multiple line segments.
    
    Args:
        surface: Pygame surface
        points: List of (x, y) screen coordinates
        color: RGB color
        width: Line width
        beam_type: BeamType enum
        hollow_ratio: Hollow core ratio
    """
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, width)
        
        # Add hollow core to curved beam
        if hollow_ratio > 0.01:
            border_px = max(2, int(width * 0.15))
            inner_w = max(0, width - (border_px * 2))
            if inner_w > 0:
                pygame.draw.lines(surface, (255, 255, 255), False, points, inner_w)


def draw_node(surface, screen_pos, is_fixed, is_hovered, color_override=None):
    """
    Draw a structural node (joint).
    
    Args:
        surface: Pygame surface
        screen_pos: (x, y) screen coordinates
        is_fixed: True for anchored nodes
        is_hovered: True when mouse is over
        color_override: Optional color to override default
    """
    if is_fixed:
        # Square anchor
        rect = pygame.Rect(screen_pos[0] - 7, screen_pos[1] - 7, 14, 14)
        pygame.draw.rect(surface, (180, 50, 50), rect)
        pygame.draw.rect(surface, (50, 20, 20), rect, 2)
    else:
        # Circle joint
        if color_override:
            color = color_override
        elif is_hovered:
            from core.constants import COLOR_CURSOR
            color = COLOR_CURSOR
        else:
            color = (60, 60, 60)
        
        pygame.draw.circle(surface, (30, 30, 30), screen_pos, 7)
        pygame.draw.circle(surface, color, screen_pos, 5)


def draw_broken_beam(surface, points, width):
    """Draw a beam with alternating red/black segments to show fracture."""
    if len(points) < 2:
        return
        
    for i in range(len(points) - 1):
        color = (255, 0, 0) if (i % 2 == 0) else (0, 0, 0)
        pygame.draw.line(surface, color, points[i], points[i + 1], width)


def create_semi_transparent_surface(width, height, color, alpha):
    """Create a surface with transparency for overlays."""
    surf = pygame.Surface((width, height))
    surf.set_alpha(alpha)
    surf.fill(color)
    return surf


def draw_text_with_background(surface, text, font, pos, text_color, bg_color, 
                              border_color=None, padding=4, border_radius=4):
    """
    Draw text with a background rectangle.
    
    Args:
        surface: Pygame surface
        text: Text string to render
        font: Pygame font object
        pos: Center position (x, y)
        text_color: RGB color for text
        bg_color: RGB color for background
        border_color: Optional RGB color for border
        padding: Pixels of padding around text
        border_radius: Corner radius for rounded rect
    """
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=pos)
    
    bg_rect = text_rect.inflate(padding * 2, padding)
    pygame.draw.rect(surface, bg_color, bg_rect, border_radius=border_radius)
    
    if border_color:
        pygame.draw.rect(surface, border_color, bg_rect, 1, border_radius=border_radius)
    
    surface.blit(text_surf, text_rect)


def interpolate_color(color1, color2, t):
    """
    Linearly interpolate between two RGB colors.
    
    Args:
        color1, color2: RGB tuples
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated RGB tuple
    """
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)