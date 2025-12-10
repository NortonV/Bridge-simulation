import math
from .beam import Beam 

class Node:
    def __init__(self, x, y, fixed=False):
        self.x = x
        self.y = y
        self.fixed = fixed 

class Bridge:
    def __init__(self):
        self.nodes = []
        self.beams = []

    def add_node(self, x, y, fixed=False):
        """Adds a unique node at (x,y). Returns existing node if found."""
        for n in self.nodes:
            if math.isclose(n.x, x, abs_tol=0.1) and math.isclose(n.y, y, abs_tol=0.1):
                return n 
        
        new_node = Node(x, y, fixed)
        self.nodes.append(new_node)
        return new_node

    def fracture_beam(self, beam):
        """
        Physically breaks a beam into two disconnected segments.
        Creates TWO separate nodes at the midpoint so the halves can separate.
        """
        # 1. Calculate Midpoint
        mx = (beam.node_a.x + beam.node_b.x) / 2
        my = (beam.node_a.y + beam.node_b.y) / 2

        # 2. Create TWO DISTINCT nodes (bypass add_node's merging logic)
        node_m1 = Node(mx, my, fixed=False)
        node_m2 = Node(mx, my, fixed=False)
        
        self.nodes.append(node_m1)
        self.nodes.append(node_m2)

        # 3. Create new beams connecting to the separate nodes
        # Left side -> M1
        b1 = self.add_beam_direct(beam.node_a, node_m1, beam.type)
        if b1: b1.hollow = beam.hollow
        
        # Right side -> M2
        b2 = self.add_beam_direct(beam.node_b, node_m2, beam.type)
        if b2: b2.hollow = beam.hollow

        # 4. Remove the original broken beam
        if beam in self.beams:
            self.beams.remove(beam)

    def split_beam(self, beam, x, y):
        """ Editor Tool: Splits a beam and WELDS them at the new node. """
        x1, y1 = beam.node_a.x, beam.node_a.y
        x2, y2 = beam.node_b.x, beam.node_b.y
        dx, dy = x2 - x1, y2 - y1
        
        if dx == 0 and dy == 0: return beam.node_a 
        
        t = ((x - x1) * dx + (y - y1) * dy) / (dx*dx + dy*dy)
        t = max(0.0, min(1.0, t)) 
        
        split_x = x1 + t * dx
        split_y = y1 + t * dy
        
        new_node = self.add_node(split_x, split_y, fixed=False)
        
        if beam in self.beams:
            self.beams.remove(beam)
        
        mat_type = beam.type
        is_hollow = beam.hollow
        
        b1 = self.add_beam_direct(beam.node_a, new_node, mat_type)
        if b1: b1.hollow = is_hollow
        
        b2 = self.add_beam_direct(new_node, beam.node_b, mat_type)
        if b2: b2.hollow = is_hollow
        
        return new_node
    
    def split_beam_with_node(self, beam, node):
        if beam not in self.beams: return
        if node == beam.node_a or node == beam.node_b: return

        self.beams.remove(beam)
        b1 = self.add_beam_direct(beam.node_a, node, beam.type)
        if b1: b1.hollow = beam.hollow
        b2 = self.add_beam_direct(node, beam.node_b, beam.type)
        if b2: b2.hollow = beam.hollow

    def split_beam_if_intersecting_node(self, beam):
        """
        Checks if any existing node lies on the beam (but is not connected to it).
        If found, splits the beam at that node.
        Returns True if a split occurred.
        """
        x1, y1 = beam.node_a.x, beam.node_a.y
        x2, y2 = beam.node_b.x, beam.node_b.y
        dx, dy = x2 - x1, y2 - y1
        beam_len_sq = dx*dx + dy*dy
        
        if beam_len_sq == 0: return False

        for node in self.nodes:
            if node is beam.node_a or node is beam.node_b: continue
            
            px, py = node.x, node.y
            
            # Project point onto line segment: t = dot(AP, AB) / |AB|^2
            dot = (px - x1) * dx + (py - y1) * dy
            t = dot / beam_len_sq
            
            # Check if projection falls strictly inside the segment
            if 0.01 < t < 0.99:
                nearest_x = x1 + t * dx
                nearest_y = y1 + t * dy
                dist_sq = (px - nearest_x)**2 + (py - nearest_y)**2
                
                # If node is very close to the line (approx < 0.1 units)
                if dist_sq < 0.01:
                    self.split_beam(beam, node.x, node.y)
                    return True
        return False

    def _get_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y

        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0: return None 

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

        if 0.001 < ua < 0.999 and 0.001 < ub < 0.999:
            ix = x1 + ua * (x2 - x1)
            iy = y1 + ua * (y2 - y1)
            return (ix, iy)
        return None

    def _get_closest_node_on_segment(self, p1, p2):
        closest_node = None
        closest_dist = float('inf')
        seg_len = math.hypot(p2.x - p1.x, p2.y - p1.y)
        
        if seg_len < 0.001: return None, float('inf')

        for node in self.nodes:
            if node is p1 or node is p2: continue
            
            d1 = math.hypot(node.x - p1.x, node.y - p1.y)
            d2 = math.hypot(p2.x - node.x, p2.y - node.y)
            
            # Strict tolerance to prevent recursion loops
            if math.isclose(d1 + d2, seg_len, abs_tol=1e-4):
                if d1 < seg_len and d2 < seg_len:
                    if d1 < closest_dist:
                        closest_dist = d1
                        closest_node = node
                    
        return closest_node, closest_dist

    def add_beam(self, node_a, node_b, material_type):
        if node_a == node_b: return []

        dx = node_b.x - node_a.x
        dy = node_b.y - node_a.y
        length = math.sqrt(dx**2 + dy**2)
        
        from core.material_manager import MaterialManager 
        mat_props = MaterialManager.MATERIALS.get(material_type)
        limit = mat_props.get("max_length")
        if limit is not None and length > limit:
            return []

        hit_beam_pt = None
        hit_beam_obj = None
        dist_beam = float('inf')

        for beam in self.beams:
            if beam.node_a in (node_a, node_b) or beam.node_b in (node_a, node_b):
                continue

            pt = self._get_intersection(node_a, node_b, beam.node_a, beam.node_b)
            if pt:
                d = math.hypot(pt[0] - node_a.x, pt[1] - node_a.y)
                if d < dist_beam:
                    dist_beam = d
                    hit_beam_pt = pt
                    hit_beam_obj = beam

        hit_node_obj, dist_node = self._get_closest_node_on_segment(node_a, node_b)

        if hit_node_obj and dist_node < dist_beam:
            beams_1 = self.add_beam(node_a, hit_node_obj, material_type)
            beams_2 = self.add_beam(hit_node_obj, node_b, material_type)
            return beams_1 + beams_2

        if hit_beam_obj and hit_beam_pt:
            split_node = self.add_node(hit_beam_pt[0], hit_beam_pt[1], fixed=False)
            old_type = hit_beam_obj.type
            old_hollow = hit_beam_obj.hollow
            if hit_beam_obj in self.beams:
                self.beams.remove(hit_beam_obj)
            
            b1 = self.add_beam_direct(hit_beam_obj.node_a, split_node, old_type)
            if b1: b1.hollow = old_hollow
            b2 = self.add_beam_direct(split_node, hit_beam_obj.node_b, old_type)
            if b2: b2.hollow = old_hollow

            beams_1 = self.add_beam(node_a, split_node, material_type)
            beams_2 = self.add_beam(split_node, node_b, material_type)
            return beams_1 + beams_2

        new_b = self.add_beam_direct(node_a, node_b, material_type)
        return [new_b] if new_b else []

    def add_beam_direct(self, node_a, node_b, material_type):
        # Check for duplicates
        for b in self.beams:
            if (b.node_a == node_a and b.node_b == node_b) or \
               (b.node_a == node_b and b.node_b == node_a):
                b.type = material_type
                return b 
        
        new_beam = Beam(node_a, node_b, material_type)
        self.beams.append(new_beam)
        return new_beam

    def get_node_at(self, x, y, threshold=0.4):
        for n in self.nodes:
            dist = math.sqrt((n.x - x)**2 + (n.y - y)**2)
            if dist < threshold:
                return n
        return None

    def get_beam_at(self, x, y, threshold=0.5):
        for beam in self.beams:
            x1, y1 = beam.node_a.x, beam.node_a.y
            x2, y2 = beam.node_b.x, beam.node_b.y
            
            dx = x2 - x1
            dy = y2 - y1
            
            if dx == 0 and dy == 0: 
                dist = math.hypot(x - x1, y - y1)
            else:
                t = ((x - x1) * dx + (y - y1) * dy) / (dx*dx + dy*dy)
                t = max(0, min(1, t))
                nearest_x = x1 + t * dx
                nearest_y = y1 + t * dy
                dist = math.hypot(x - nearest_x, y - nearest_y)
            
            if dist < threshold:
                return beam
        return None