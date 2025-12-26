"""
Mathematical utility functions for geometry and physics calculations.
"""
import math
import numpy as np


def hermite_spline_point(t, p1, p2, rot1, rot2, length):
    """
    Calculate a point on a cubic Hermite spline curve.
    
    Used for rendering and collision detection of deformed beams.
    
    Args:
        t: Parameter along curve (0 to 1)
        p1, p2: Start and end points (x, y)
        rot1, rot2: Rotations at endpoints (radians, relative to chord)
        length: Deformed length of the beam
        
    Returns:
        (x, y) point on the curve
    """
    # Hermite basis functions for tangent control
    h1 = t**3 - 2*t**2 + t
    h2 = t**3 - t**2
    
    # Perpendicular deflection from chord
    v = length * (h1 * rot1 + h2 * rot2)
    # Distance along chord
    u = t * length
    
    # Chord angle
    chord_dx = p2[0] - p1[0]
    chord_dy = p2[1] - p1[1]
    psi = math.atan2(chord_dy, chord_dx)
    
    # Transform to global coordinates
    cp, sp = math.cos(psi), math.sin(psi)
    x = p1[0] + u * cp - v * sp
    y = p1[1] + u * sp + v * cp
    
    return x, y


def normalize_angle(angle):
    """Normalize angle to range [-π, π]."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def point_to_segment_distance(point, seg_start, seg_end):
    """
    Calculate shortest distance from a point to a line segment.
    
    Returns:
        (distance, t) where t is the parameter along the segment (0 to 1)
    """
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end
    
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1), 0.0
    
    # Project point onto line
    t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
    t = max(0.0, min(1.0, t))
    
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    dist = math.hypot(px - nearest_x, py - nearest_y)
    
    return dist, t


def segment_intersection(p1, p2, p3, p4):
    """
    Find intersection point of two line segments.
    
    Args:
        p1, p2: Endpoints of first segment (must have .x and .y attributes)
        p3, p4: Endpoints of second segment
        
    Returns:
        (x, y) intersection point or None if no intersection
    """
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:
        return None

    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

    # Check if intersection is within both segments (with small margin to avoid endpoints)
    if 0.001 < ua < 0.999 and 0.001 < ub < 0.999:
        ix = x1 + ua * (x2 - x1)
        iy = y1 + ua * (y2 - y1)
        return (ix, iy)
    
    return None


def rotation_matrix_2d(angle):
    """Create a 2D rotation matrix."""
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s], [s, c]])


def quadratic_bezier_points(p0, p1, p2, num_points):
    """
    Generate points along a quadratic Bézier curve.
    
    Used for arch tool preview.
    
    Args:
        p0, p1, p2: Control points (x, y)
        num_points: Number of points to generate
        
    Returns:
        List of (x, y) points
    """
    points = []
    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        points.append((x, y))
    return points