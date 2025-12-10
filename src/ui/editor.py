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

    def play_place_sound(self, mat_type):
        if mat_type == BeamType.VINE:
            self.audio.play_sfx("vine_place")
        else:
            self.audio.play_sfx("wood_place")

    def handle_continuous_input(self, world_pos):
        """Called every frame to handle holding down mouse buttons (e.g., Delete)."""
        wx, wy = world_pos
        mouse_pressed = pygame.mouse.get_pressed()
        tool = self.toolbar.selected_tool
        
        # Recalculate hover each frame for smooth deletion
        self.hover_node = self.bridge.get_node_at(wx, wy)
        self.hover_beam = None
        if not self.hover_node:
            self.hover_beam = self.bridge.get_beam_at(wx, wy)

        # HOLD LEFT CLICK -> DELETE
        if mouse_pressed[0] and tool["type"] == "DELETE":
            # 1. DELETE NODE (Only if NOT fixed/red)
            if self.hover_node and not self.hover_node.fixed:
                to_remove = [b for b in self.bridge.beams if b.node_a == self.hover_node or b.node_b == self.hover_node]
                for b in to_remove: 
                    if b in self.bridge.beams: self.bridge.beams.remove(b)
                if self.hover_node in self.bridge.nodes:
                    self.bridge.nodes.remove(self.hover_node)
                self.hover_node = None
                return
            
            # 2. DELETE BEAM
            if self.hover_beam:
                # We allow deleting beams connected to red nodes, 
                # but NOT deleting the red nodes themselves (handled above).
                if self.hover_beam in self.bridge.beams:
                    self.bridge.beams.remove(self.hover_beam)
                self.hover_beam = None
                return

    def handle_input(self, event, world_pos):
        wx, wy = world_pos
        self.hover_node = self.bridge.get_node_at(wx, wy)
        self.hover_beam = None
        if not self.hover_node:
            self.hover_beam = self.bridge.get_beam_at(wx, wy)
        
        tool = self.toolbar.selected_tool
        tool_type = tool["type"]

        # --- DRAGGING LOGIC ---
        if event.type == pygame.MOUSEMOTION and self.drag_node:
            self.drag_node.x = wx
            self.drag_node.y = wy
            # Auto-anchor if below ground (0 floor)
            if self.drag_node.y <= 0: self.drag_node.fixed = True
            
            # Note: We do NOT un-fix a node if it is dragged into the air. 
            # If it was red (fixed), it stays red.

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: # Right Click Start Drag
                if self.hover_node:
                    self.drag_node = self.hover_node
            
            if event.button == 1: # Left Click
                if tool_type == "DELETE":
                    # 1. DELETE NODE (Only if NOT fixed)
                    if self.hover_node and not self.hover_node.fixed:
                        to_remove = [b for b in self.bridge.beams if b.node_a == self.hover_node or b.node_b == self.hover_node]
                        for b in to_remove: self.bridge.beams.remove(b)
                        self.bridge.nodes.remove(self.hover_node)
                        self.hover_node = None
                        return
                    # 2. DELETE BEAM
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
            # --- Right Click Release (Drop Node / Merge) ---
            if event.button == 3 and self.drag_node:
                # 1. Check for Node Merge
                # FIX: Explicitly find a node that is NOT the one we are dragging
                target_node = None
                for n in self.bridge.nodes:
                    if n == self.drag_node: continue
                    dist = math.hypot(n.x - self.drag_node.x, n.y - self.drag_node.y)
                    if dist < 0.4: # Same threshold as get_node_at
                        target_node = n
                        break
                
                if target_node:
                    # --- NODE MERGE LOGIC ---
                    
                    node_to_keep = None
                    node_to_remove = None
                    respawn_red_node = False
                    
                    drag_fixed = self.drag_node.fixed
                    target_fixed = target_node.fixed
                    
                    # Case 1: Red + Red
                    if drag_fixed and target_fixed:
                        # Delete one, keep target, respawn new red node at Center
                        node_to_keep = target_node
                        node_to_remove = self.drag_node
                        respawn_red_node = True
                    
                    # Case 2: Red dragged onto Normal (Red wins)
                    elif drag_fixed and not target_fixed:
                        node_to_keep = self.drag_node
                        node_to_remove = target_node
                        
                    # Case 3: Normal dragged onto Red (Red wins)
                    elif not drag_fixed and target_fixed:
                        node_to_keep = target_node
                        node_to_remove = self.drag_node
                        
                    # Case 4: Normal + Normal
                    else:
                        node_to_keep = target_node
                        node_to_remove = self.drag_node
                    
                    # Redirect beams
                    beams_to_remove = []
                    for beam in self.bridge.beams:
                        if beam.node_a == node_to_remove:
                            beam.node_a = node_to_keep
                        elif beam.node_b == node_to_remove:
                            beam.node_b = node_to_keep
                        
                        if beam.node_a == beam.node_b:
                            beams_to_remove.append(beam)
                    
                    for b in beams_to_remove:
                        if b in self.bridge.beams: self.bridge.beams.remove(b)
                    
                    if node_to_remove in self.bridge.nodes:
                        self.bridge.nodes.remove(node_to_remove)
                        
                    # RESPAWN LOGIC for Red+Red merge
                    if respawn_red_node:
                        # Try to spawn at (0, 10), then (0, 15), etc.
                        sx, sy = 0, 10
                        while True:
                            existing = self.bridge.get_node_at(sx, sy)
                            
                            if not existing:
                                # Spot is free, spawn new red node here
                                self.bridge.add_node(sx, sy, fixed=True)
                                break
                            
                            if not existing.fixed:
                                # Spot occupied by NON-RED node. Overwrite it.
                                # "Overwrite" implies converting it to a red node.
                                existing.fixed = True
                                existing.x = sx
                                existing.y = sy
                                existing.start_x = sx
                                existing.start_y = sy
                                break
                            
                            # Spot occupied by RED node. Move up 1 big square (5m).
                            sy += 5
                            if sy > 100: break # Safety break to prevent infinite loop
                        
                    self.audio.play_sfx("wood_place")
                
                else:
                    # 2. Check for Beam Snap (New Feature)
                    target_beam = self.bridge.get_beam_at(self.drag_node.x, self.drag_node.y)
                    if target_beam:
                         # We dropped an existing node onto a beam.
                         # We want to split that beam and insert this node.
                         self.bridge.split_beam_with_node(target_beam, self.drag_node)
                         self.audio.play_sfx("wood_place")

                    # Just playing sound if valid placement
                    else:
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
                if self.toolbar.selected_tool["type"] == "DELETE": 
                    # Only turn red if it is deletable (not fixed)
                    if not node.fixed: color = (255, 0, 0) 
                else: color = COLOR_CURSOR 
            pygame.draw.circle(surface, color, pos, 7)
            pygame.draw.circle(surface, (255,255,255), pos, 7, 2)

        # Draw Ghost Drag Line
        if self.start_node:
            start = self.grid.world_to_screen(self.start_node.x, self.start_node.y)
            mx, my = pygame.mouse.get_pos()
            tool_color = self.toolbar.selected_tool["color"]
            pygame.draw.line(surface, tool_color, start, (mx, my), 3)