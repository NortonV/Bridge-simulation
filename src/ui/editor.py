"""
Interactive editor for building bridge structures.
"""
import pygame
import math
from core.constants import *
from entities.beam import BeamType
from core.material_manager import MaterialManager
from utils.math_utils import quadratic_bezier_points
from utils.render_utils import draw_beam_texture, draw_node


class Editor:
    """
    Handles user interaction for building and modifying bridges.
    
    Supports:
    - Placing and connecting nodes/beams
    - Dragging and merging nodes
    - Deleting elements
    - Arch tool for curved structures
    """
    
    # Node merge threshold (meters)
    MERGE_THRESHOLD = 0.4
    # Beam selection threshold (meters)
    BEAM_SELECT_THRESHOLD = 0.5
    # Arch tool height sensitivity (Higher = more responsive vertical movement)
    ARCH_SENSITIVITY = 2.0
    
    def __init__(self, grid, bridge, toolbar, audio_manager):
        self.grid = grid
        self.bridge = bridge
        self.toolbar = toolbar
        self.audio = audio_manager
        
        # Interaction state
        self.start_node = None  # First node when drawing beam
        self.hover_node = None  # Node under cursor
        self.hover_beam = None  # Beam under cursor
        self.drag_node = None   # Node being dragged
        
        # Arch tool state
        self.arch_mode = False
        self.arch_stage = 0  # 0: select start, 1: position control point
        self.arch_end_node = None

    def toggle_arch_mode(self):
        """Toggle arch drawing mode on/off."""
        self.arch_mode = not self.arch_mode
        self.arch_stage = 0
        self.arch_end_node = None
        self.start_node = None
        return self.arch_mode

    def handle_continuous_input(self, world_pos):
        """
        Handle continuous input (mouse held down).
        
        Used for delete tool to continuously remove elements.
        """
        wx, wy = world_pos
        mouse_pressed = pygame.mouse.get_pressed()
        tool = self.toolbar.selected_tool
        
        # Don't update hover during arch control point selection
        if self.arch_stage == 1:
            self.hover_node = None
            self.hover_beam = None
            return

        # Update what's under cursor
        self.hover_node = self.bridge.get_node_at(wx, wy)
        self.hover_beam = None
        if not self.hover_node:
            self.hover_beam = self.bridge.get_beam_at(wx, wy)

        # Continuous deletion
        if mouse_pressed[0] and tool["type"] == "DELETE":
            self._handle_continuous_delete()

    def _handle_continuous_delete(self):
        """Delete hovered element continuously while mouse held."""
        if self.hover_node and not self.hover_node.fixed:
            # Remove all beams connected to this node
            connected_beams = [b for b in self.bridge.beams 
                             if b.node_a == self.hover_node or b.node_b == self.hover_node]
            for beam in connected_beams:
                if beam in self.bridge.beams:
                    self.bridge.beams.remove(beam)
                    self.audio.play_sfx("wood_place")
            
            # Remove the node
            if self.hover_node in self.bridge.nodes:
                self.bridge.nodes.remove(self.hover_node)
                self.audio.play_sfx("wood_place")
            
            self.hover_node = None
        
        elif self.hover_beam:
            if self.hover_beam in self.bridge.beams:
                self.bridge.beams.remove(self.hover_beam)
                self.audio.play_sfx("wood_place")
            self.hover_beam = None

    def handle_input(self, event, world_pos):
        """Handle discrete input events (clicks, releases)."""
        wx, wy = world_pos
        
        # Update hover state
        if self.arch_stage == 0:
            self.hover_node = self.bridge.get_node_at(wx, wy)
            self.hover_beam = None
            if not self.hover_node:
                self.hover_beam = self.bridge.get_beam_at(wx, wy)
        else:
            self.hover_node = None
            self.hover_beam = None
        
        tool = self.toolbar.selected_tool
        tool_type = tool["type"]

        if event.type == pygame.MOUSEMOTION and self.drag_node:
            self._handle_node_drag(wx, wy)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # Right click
                self._handle_right_click()
            elif event.button == 1:  # Left click
                self._handle_left_click(wx, wy, tool_type)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self._handle_right_release()
            elif event.button == 1:
                self._handle_left_release(wx, wy, tool_type)

    def _handle_node_drag(self, wx, wy):
        """Update dragged node position."""
        self.drag_node.x = wx
        self.drag_node.y = wy
        # Nodes at or above ground level become fixed anchors
        if self.drag_node.y <= 0:
            self.drag_node.fixed = True
    
    def _handle_right_click(self):
        """Handle right mouse button press."""
        # Cancel current operation
        if self.start_node:
            self.start_node = None
            if self.arch_stage == 1:
                self.arch_stage = 0
                self.arch_end_node = None
        elif self.arch_stage == 1:
            self.arch_stage = 0
            self.start_node = None
            self.arch_end_node = None
        elif self.hover_node:
            # Start dragging hovered node
            self.drag_node = self.hover_node
    
    def _handle_left_click(self, wx, wy, tool_type):
        """Handle left mouse button press."""
        if self.arch_stage == 1:
            # Complete arch with control point
            self._build_arch_curve(wx, wy, tool_type)
            self.arch_stage = 0
            self.start_node = None
            self.arch_end_node = None
            self.audio.play_sfx("wood_place")
        
        elif tool_type == "DELETE":
            pass  # Deletion handled by continuous input
        
        elif self.hover_node:
            # Start drawing from existing node
            self.start_node = self.hover_node
        
        elif self.hover_beam:
            # Split beam and start drawing from split point
            self.start_node = self.bridge.split_beam(self.hover_beam, wx, wy)
            self.audio.play_sfx("wood_place")
        
        else:
            # Create new node
            is_anchor = (wy <= 0)
            self.start_node = self.bridge.add_node(wx, wy, is_anchor)

    def _handle_right_release(self):
        """Handle right mouse button release (end of drag)."""
        if not self.drag_node:
            return
        
        # Try to merge with nearby node
        target_node = self._find_merge_target()
        
        if target_node:
            self._merge_nodes(self.drag_node, target_node)
        else:
            # Try to snap to nearby beam
            target_beam = self.bridge.get_beam_at(
                self.drag_node.x, self.drag_node.y
            )
            if target_beam:
                self.bridge.connect_node_to_beam(self.drag_node, target_beam)
                self.audio.play_sfx("wood_place")
        
        self.drag_node = None

    def _find_merge_target(self):
        """Find a node close enough to merge with dragged node."""
        for node in self.bridge.nodes:
            if node == self.drag_node:
                continue
            
            dist = math.hypot(
                node.x - self.drag_node.x,
                node.y - self.drag_node.y
            )
            
            if dist < self.MERGE_THRESHOLD:
                return node
        
        return None

    def _merge_nodes(self, node_to_remove, node_to_keep):
        """
        Merge two nodes by redirecting all beams.
        
        Prefers to keep fixed nodes.
        """
        # Swap if we should keep the other node
        if node_to_remove.fixed and not node_to_keep.fixed:
            node_to_remove, node_to_keep = node_to_keep, node_to_remove
        
        # Redirect all beams
        beams_to_remove = []
        for beam in self.bridge.beams:
            if beam.node_a == node_to_remove:
                beam.node_a = node_to_keep
            elif beam.node_b == node_to_remove:
                beam.node_b = node_to_keep
            
            # Mark self-referencing beams for removal
            if beam.node_a == beam.node_b:
                beams_to_remove.append(beam)
        
        # Clean up
        for beam in beams_to_remove:
            if beam in self.bridge.beams:
                self.bridge.beams.remove(beam)
        
        if node_to_remove in self.bridge.nodes:
            self.bridge.nodes.remove(node_to_remove)
        
        self.audio.play_sfx("wood_place")

    def _handle_left_release(self, wx, wy, tool_type):
        """Handle left mouse button release (complete beam)."""
        if not self.start_node or tool_type == "DELETE":
            return
        
        # Find or create end node
        end_node = self.hover_node
        if not end_node:
            if self.hover_beam:
                end_node = self.bridge.split_beam(self.hover_beam, wx, wy)
                self.audio.play_sfx("wood_place")
            else:
                is_anchor = (wy <= 0)
                end_node = self.bridge.add_node(wx, wy, is_anchor)
        
        # Create beam
        if self.start_node != end_node:
            if self.arch_mode:
                # Start arch mode stage 2
                if self.arch_stage == 0:
                    self.arch_end_node = end_node
                    self.arch_stage = 1
            else:
                # Create straight beam
                created = self.bridge.add_beam(self.start_node, end_node, tool_type)
                if created:
                    self.audio.play_sfx("wood_place")
        
        # Reset unless waiting for arch control point
        if not (self.arch_mode and self.arch_stage == 1):
            self.start_node = None

    def _build_arch_curve(self, cx, cy, mat_type):
        """
        Create an arch using quadratic Bézier curve.
        
        Args:
            cx, cy: Control point position (world coordinates)
            mat_type: Material type for beams
        """
        p0 = (self.start_node.x, self.start_node.y)
        p2 = (self.arch_end_node.x, self.arch_end_node.y)
        mid_y = (p0[1] + p2[1]) / 2
        cy = mid_y + (cy - mid_y) * self.ARCH_SENSITIVITY
        p1 = (cx, cy)
        
        segments = 8
        prev_node = self.start_node
        
        for i in range(1, segments + 1):
            t = i / segments
            
            # Calculate point on Bézier curve
            bx = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
            by = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
            
            # Snap to grid
            bx = round(bx * 2) / 2
            by = round(by * 2) / 2
            
            # Use end node for last segment
            if i == segments:
                current_node = self.arch_end_node
            else:
                current_node = self.bridge.add_node(bx, by, fixed=(by <= 0))

            # Skip if nodes are the same or at same position (prevents zero-length beams)
            if current_node != prev_node:
                dx = current_node.x - prev_node.x
                dy = current_node.y - prev_node.y
                if math.hypot(dx, dy) > 0.01:  # Only create beam if length > 1cm
                    self.bridge.add_beam(prev_node, current_node, mat_type)
                    prev_node = current_node
                # If too close, skip this node and keep prev_node as-is
            # If same node, skip and keep prev_node as-is

    def draw(self, surface):
        """Draw all bridge elements and editor overlays."""
        # Draw beams
        for beam in self.bridge.beams:
            self._draw_beam(surface, beam)
        
        # Draw nodes
        for node in self.bridge.nodes:
            self._draw_node(surface, node)
        
        # Draw preview/guide lines
        self._draw_preview(surface)

    def _draw_beam(self, surface, beam):
        """Draw a single beam with appropriate styling."""
        start = self.grid.world_to_screen(beam.node_a.x, beam.node_a.y)
        end = self.grid.world_to_screen(beam.node_b.x, beam.node_b.y)
        color = beam.color
        
        # Determine visual width
        props = MaterialManager.get_properties(beam.type, hollow_ratio=beam.hollow_ratio)
        width = max(4, int(props['thickness'] * PPM))
        
        # Highlight if hovering with delete tool
        if self.toolbar.selected_tool["type"] == "DELETE" and beam == self.hover_beam:
            color = (200, 50, 50)
            width += 4
        
        draw_beam_texture(
            surface, start, end, beam.type, width, color, beam.hollow_ratio
        )

    def _draw_node(self, surface, node):
        """Draw a single node with appropriate styling."""
        pos = self.grid.world_to_screen(node.x, node.y)
        
        # Determine color override for hover/delete
        color_override = None
        if node == self.hover_node:
            if self.toolbar.selected_tool["type"] == "DELETE" and not node.fixed:
                color_override = (200, 50, 50)
            else:
                color_override = COLOR_CURSOR
        
        draw_node(surface, pos, node.fixed, node == self.hover_node, color_override)

    def _draw_preview(self, surface):
        """Draw preview lines and arch curves."""
        mx, my = pygame.mouse.get_pos()
        tool_color = self.toolbar.selected_tool["color"]
        
        if self.arch_mode and self.arch_stage == 1:
            # Draw arch preview
            self._draw_arch_preview(surface, mx, my, tool_color)
        elif self.start_node:
            # Draw straight line preview
            start = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
            pygame.draw.line(surface, tool_color, start, (mx, my), 2)
            pygame.draw.circle(surface, tool_color, (mx, my), 4)

    def _draw_arch_preview(self, surface, mx, my, color):
        """Draw curved arch preview."""
        s_pos = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
        e_pos = self.grid.world_to_screen(self.arch_end_node.x, self.arch_end_node.y)

        mid_y_screen = (s_pos[1] + e_pos[1]) / 2
        target_my = mid_y_screen + (my - mid_y_screen) * self.ARCH_SENSITIVITY
        
        # Generate curve points
        points = quadratic_bezier_points(s_pos, (mx, target_my), e_pos, 21)
        
        # Draw curve and endpoints
        pygame.draw.lines(surface, color, False, points, 2)
        pygame.draw.circle(surface, color, s_pos, 4)
        pygame.draw.circle(surface, color, e_pos, 4)