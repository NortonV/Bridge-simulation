import pygame
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

    def play_place_sound(self, mat_type):
        if mat_type == BeamType.VINE:
            self.audio.play_sfx("vine_place")
        else:
            self.audio.play_sfx("wood_place")

    def handle_continuous_input(self, world_pos):
        """Called every frame to handle hovering and dragging updates."""
        wx, wy = world_pos
        
        # 1. Update Hover State
        self.hover_node = self.bridge.get_node_at(wx, wy)
        self.hover_beam = None
        if not self.hover_node:
            self.hover_beam = self.bridge.get_beam_at(wx, wy)
            
        # 2. Update Dragging Position
        if self.drag_node:
            self.drag_node.x = wx
            self.drag_node.y = wy
            # Auto-fix anchor if dragged below ground
            if self.drag_node.y <= 0: self.drag_node.fixed = True
            else: self.drag_node.fixed = False

    def handle_input(self, event, world_pos):
        wx, wy = world_pos
        tool = self.toolbar.selected_tool
        tool_type = tool["type"]

        # NOTE: Hover/Drag updates are now in handle_continuous_input
        # We focus on discrete events here (Clicks)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: # Right Click Start Drag
                if self.hover_node:
                    self.drag_node = self.hover_node
            
            if event.button == 1: # Left Click
                if tool_type == "DELETE":
                    if self.hover_node and not self.hover_node.fixed:
                        to_remove = [b for b in self.bridge.beams if b.node_a == self.hover_node or b.node_b == self.hover_node]
                        for b in to_remove: self.bridge.beams.remove(b)
                        self.bridge.nodes.remove(self.hover_node)
                        self.hover_node = None
                        return
                    if self.hover_beam:
                        # Attempt to split the beam by existing nodes first
                        while self.bridge.split_beam_if_intersecting_node(self.hover_beam):
                            self.hover_beam = self.bridge.get_beam_at(wx, wy)
                            if not self.hover_beam: break
                        
                        if self.hover_beam:
                            self.bridge.beams.remove(self.hover_beam)
                            self.hover_beam = None
                        return
                    return
                
                # --- BUILD LOGIC ---
                if self.hover_node:
                    # Case A: Clicked on existing node
                    self.start_node = self.hover_node
                elif self.hover_beam:
                    # Case B: Clicked on a beam -> SPLIT IT
                    self.start_node = self.bridge.split_beam(self.hover_beam, wx, wy)
                    self.play_place_sound(self.hover_beam.type)
                else:
                    # Case C: Clicked in empty space -> Create new node
                    is_anchor = (wy <= 0)
                    self.start_node = self.bridge.add_node(wx, wy, is_anchor)

        elif event.type == pygame.MOUSEBUTTONUP:
            # --- Right Click Release (Drop Node) ---
            if event.button == 3 and self.drag_node:
                connected = [b for b in self.bridge.beams if b.node_a == self.drag_node or b.node_b == self.drag_node]
                if connected:
                    has_wood = any(b.type in [BeamType.WOOD, BeamType.BAMBOO] for b in connected)
                    if has_wood: self.audio.play_sfx("wood_place")
                    else: self.audio.play_sfx("vine_place")
                self.drag_node = None

            # --- Left Click Release (Build Beam) ---
            if event.button == 1 and self.start_node:
                if tool_type != "DELETE":
                    end_node = self.hover_node
                    if not end_node:
                        is_anchor = (wy <= 0)
                        end_node = self.bridge.add_node(wx, wy, is_anchor)
                    
                    if self.start_node != end_node:
                        created_beams = self.bridge.add_beam(self.start_node, end_node, tool_type)
                        if created_beams:
                            for b in created_beams:
                                b.hollow = MaterialManager.PLACEMENT_MODE_HOLLOW
                            self.play_place_sound(tool_type)
                self.start_node = None

    def draw(self, surface):
        # Draw Beams
        for beam in self.bridge.beams:
            start = self.grid.world_to_screen(beam.node_a.x, beam.node_a.y)
            end = self.grid.world_to_screen(beam.node_b.x, beam.node_b.y)
            color = beam.color
            width = 6
            if self.toolbar.selected_tool["type"] == "DELETE" and beam == self.hover_beam:
                color = (255, 0, 0)
                width = 10
            
            pygame.draw.line(surface, color, start, end, width)
            if beam.hollow:
                pygame.draw.line(surface, (255,255,255), start, end, 2)

        # Draw Nodes
        for node in self.bridge.nodes:
            pos = self.grid.world_to_screen(node.x, node.y)
            color = (200, 50, 50) if node.fixed else (50, 50, 50)
            if node == self.hover_node: 
                if self.toolbar.selected_tool["type"] == "DELETE": color = (255, 0, 0) 
                else: color = COLOR_CURSOR 
            pygame.draw.circle(surface, color, pos, 7)
            pygame.draw.circle(surface, (255,255,255), pos, 7, 2)

        # Draw Ghost Drag Line
        if self.start_node:
            start = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
            mx, my = pygame.mouse.get_pos()
            tool_color = self.toolbar.selected_tool["color"]
            pygame.draw.line(surface, tool_color, start, (mx, my), 3)