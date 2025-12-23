import pygame
import math
from core.constants import *
from entities.beam import BeamType
from core.material_manager import MaterialManager

class Editor:
    def __init__(self, grid, bridge, toolbar, audio_manager):
        self.grid = grid
        self.bridge = bridge
        self.toolbar = toolbar
        self.audio = audio_manager 
        
        self.start_node = None
        self.hover_node = None
        self.hover_beam = None
        self.drag_node = None
        
        self.arch_mode = False
        self.arch_stage = 0 
        self.arch_end_node = None

    def toggle_arch_mode(self):
        self.arch_mode = not self.arch_mode
        self.arch_stage = 0
        self.arch_end_node = None
        self.start_node = None
        return self.arch_mode

    def play_place_sound(self, mat_type):
        self.audio.play_sfx("wood_place")

    def handle_continuous_input(self, world_pos):
        wx, wy = world_pos
        mouse_pressed = pygame.mouse.get_pressed()
        tool = self.toolbar.selected_tool
        
        if self.arch_stage == 1:
            self.hover_node = None
            self.hover_beam = None
            return

        self.hover_node = self.bridge.get_node_at(wx, wy)
        self.hover_beam = None
        if not self.hover_node:
            self.hover_beam = self.bridge.get_beam_at(wx, wy)

        if mouse_pressed[0] and tool["type"] == "DELETE":
            if self.hover_node and not self.hover_node.fixed:
                to_remove = [b for b in self.bridge.beams if b.node_a == self.hover_node or b.node_b == self.hover_node]
                for b in to_remove: 
                    if b in self.bridge.beams: self.bridge.beams.remove(b)
                if self.hover_node in self.bridge.nodes:
                    self.bridge.nodes.remove(self.hover_node)
                self.hover_node = None
                return
            
            if self.hover_beam:
                if self.hover_beam in self.bridge.beams:
                    self.bridge.beams.remove(self.hover_beam)
                self.hover_beam = None
                return

    def handle_input(self, event, world_pos):
        wx, wy = world_pos
        
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
            self.drag_node.x = wx
            self.drag_node.y = wy
            if self.drag_node.y <= 0: self.drag_node.fixed = True
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: 
                if self.start_node:
                    self.start_node = None
                    if self.arch_stage == 1:
                        self.arch_stage = 0
                        self.arch_end_node = None
                    return
                
                if self.arch_stage == 1:
                    self.arch_stage = 0
                    self.start_node = None
                    self.arch_end_node = None
                elif self.hover_node:
                    self.drag_node = self.hover_node
            
            if event.button == 1: 
                if self.arch_stage == 1:
                    self.build_arch_curve(wx, wy, tool_type)
                    self.arch_stage = 0
                    self.start_node = None
                    self.arch_end_node = None
                    self.play_place_sound(tool_type)
                
                elif tool_type == "DELETE":
                    pass
                elif self.hover_node:
                    self.start_node = self.hover_node
                elif self.hover_beam:
                    self.start_node = self.bridge.split_beam(self.hover_beam, wx, wy)
                    self.play_place_sound(self.hover_beam.type)
                else:
                    is_anchor = (wy <= 0)
                    self.start_node = self.bridge.add_node(wx, wy, is_anchor)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3 and self.drag_node:
                target_node = None
                for n in self.bridge.nodes:
                    if n == self.drag_node: continue
                    dist = math.hypot(n.x - self.drag_node.x, n.y - self.drag_node.y)
                    if dist < 0.4:
                        target_node = n
                        break
                
                if target_node:
                    node_to_keep = target_node
                    node_to_remove = self.drag_node
                    
                    if self.drag_node.fixed and not target_node.fixed:
                        node_to_keep = self.drag_node
                        node_to_remove = target_node
                    
                    beams_to_rm = []
                    for beam in self.bridge.beams:
                        if beam.node_a == node_to_remove: beam.node_a = node_to_keep
                        elif beam.node_b == node_to_remove: beam.node_b = node_to_keep
                        if beam.node_a == beam.node_b: beams_to_rm.append(beam)
                    
                    for b in beams_to_rm: 
                        if b in self.bridge.beams: self.bridge.beams.remove(b)
                    
                    if node_to_remove in self.bridge.nodes:
                        self.bridge.nodes.remove(node_to_remove)
                    
                    self.audio.play_sfx("wood_place")
                else:
                    target_beam = self.bridge.get_beam_at(self.drag_node.x, self.drag_node.y)
                    if target_beam:
                         self.bridge.connect_node_to_beam(self.drag_node, target_beam)
                         self.audio.play_sfx("wood_place")
                
                self.drag_node = None

            if event.button == 1 and self.start_node:
                if tool_type != "DELETE":
                    end_node = self.hover_node
                    if not end_node:
                        if self.hover_beam:
                            end_node = self.bridge.split_beam(self.hover_beam, wx, wy)
                            self.play_place_sound(self.hover_beam.type)
                        else:
                            is_anchor = (wy <= 0)
                            end_node = self.bridge.add_node(wx, wy, is_anchor)
                    
                    if self.start_node != end_node:
                        if self.arch_mode:
                            if self.arch_stage == 0:
                                self.arch_end_node = end_node
                                self.arch_stage = 1
                        else:
                            created = self.bridge.add_beam(self.start_node, end_node, tool_type)
                            if created:
                                self.play_place_sound(tool_type)
                
                if not (self.arch_mode and self.arch_stage == 1):
                     self.start_node = None

    def build_arch_curve(self, cx, cy, mat_type):
        p0 = (self.start_node.x, self.start_node.y)
        p2 = (self.arch_end_node.x, self.arch_end_node.y)
        p1 = (cx, cy)
        
        segments = 8
        prev_node = self.start_node
        
        for i in range(1, segments + 1):
            t = i / segments
            bx = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
            by = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
            
            bx = round(bx * 2) / 2
            by = round(by * 2) / 2
            
            if i == segments:
                current_node = self.arch_end_node
            else:
                current_node = self.bridge.add_node(bx, by, fixed=(by<=0))
            
            self.bridge.add_beam(prev_node, current_node, mat_type)
            prev_node = current_node

    def draw_textured_beam(self, surface, start, end, beam_type, width, color, hollow_ratio):
        # Improved drawing logic
        # 1. Draw subtle shadow for contrast
        shadow_off = 2
        pygame.draw.line(surface, (10, 15, 10), (start[0]+shadow_off, start[1]+shadow_off), 
                        (end[0]+shadow_off, end[1]+shadow_off), width)
        
        # 2. Draw Main Beam
        pygame.draw.line(surface, color, start, end, width)
        
        if beam_type == BeamType.BAMBOO:
            for t in [0.25, 0.5, 0.75]:
                tx = start[0] + (end[0] - start[0]) * t
                ty = start[1] + (end[1] - start[1]) * t
                pygame.draw.circle(surface, (50, 60, 40), (int(tx), int(ty)), width // 2 + 1)
                pygame.draw.circle(surface, (150, 180, 100), (int(tx), int(ty)), width // 2 - 1)
                
        elif beam_type == BeamType.WOOD:
            pygame.draw.line(surface, (80, 40, 10), start, end, 1)
        
        elif beam_type == BeamType.STEEL:
            pygame.draw.line(surface, (150, 160, 170), start, end, 2)

        elif beam_type == BeamType.SPAGHETTI:
             dx = end[0] - start[0]
             dy = end[1] - start[1]
             L = math.hypot(dx, dy)
             if L > 0:
                 nx = -dy / L
                 ny = dx / L
                 offsets = [-1.5, 0, 1.5]
                 for off in offsets:
                     ox, oy = nx * off, ny * off
                     s_off = (start[0] + ox, start[1] + oy)
                     e_off = (end[0] + ox, end[1] + oy)
                     pygame.draw.line(surface, (255, 255, 150), s_off, e_off, 1)

        # Fix Hollow visibility
        if hollow_ratio > 0.0:
            # Calculate border size: at least 1.5 pixels or 15% of width
            border_px = max(2, int(width * 0.15)) 
            inner_w = max(0, width - (border_px * 2))
            
            if inner_w > 0:
                pygame.draw.line(surface, (255, 255, 255), start, end, inner_w)

    def draw(self, surface):
        for beam in self.bridge.beams:
            start = self.grid.world_to_screen(beam.node_a.x, beam.node_a.y)
            end = self.grid.world_to_screen(beam.node_b.x, beam.node_b.y)
            color = beam.color
            
            # Increased base width for better visibility
            props = MaterialManager.get_properties(beam.type)
            width = max(4, int(props['thickness'] * PPM)) 
            
            if self.toolbar.selected_tool["type"] == "DELETE" and beam == self.hover_beam:
                color = (200, 50, 50)
                width += 4
            
            current_hollow_ratio = beam.hollow_ratio
            self.draw_textured_beam(surface, start, end, beam.type, width, color, current_hollow_ratio)

        for node in self.bridge.nodes:
            pos = self.grid.world_to_screen(node.x, node.y)
            if node.fixed:
                rect = pygame.Rect(pos[0]-7, pos[1]-7, 14, 14)
                pygame.draw.rect(surface, (180, 50, 50), rect) 
                pygame.draw.rect(surface, (50, 20, 20), rect, 2)
            else:
                color = (60, 60, 60)
                if node == self.hover_node: 
                    if self.toolbar.selected_tool["type"] == "DELETE": 
                        if not node.fixed: color = (200, 50, 50) 
                    else: color = COLOR_CURSOR 
                pygame.draw.circle(surface, (30, 30, 30), pos, 7) 
                pygame.draw.circle(surface, color, pos, 5)        

        mx, my = pygame.mouse.get_pos()
        tool_color = self.toolbar.selected_tool["color"]

        if self.arch_mode and self.arch_stage == 1:
            s_pos = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
            e_pos = self.grid.world_to_screen(self.arch_end_node.x, self.arch_end_node.y)
            p0 = s_pos
            p1 = (mx, my)
            p2 = e_pos
            points = []
            for i in range(21): # Smoother arch line
                t = i / 20
                bx = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                by = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                points.append((bx, by))
            pygame.draw.lines(surface, tool_color, False, points, 2)
            pygame.draw.circle(surface, tool_color, s_pos, 4)
            pygame.draw.circle(surface, tool_color, e_pos, 4)
            
        elif self.start_node:
            start = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
            pygame.draw.line(surface, tool_color, start, (mx, my), 2)
            pygame.draw.circle(surface, tool_color, (mx, my), 4)