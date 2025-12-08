import math
from core.material_manager import MaterialManager

class StaticSolver:
    def __init__(self, bridge_data):
        self.nodes = bridge_data.nodes
        self.beams = bridge_data.beams
        self.results = {} 
        self.error_msg = ""

    def is_stable(self):
        J = len(self.nodes)
        M = len(self.beams)
        R = sum(2 for n in self.nodes if n.fixed)
        if M + R < 2 * J:
            self.error_msg = "Unstable: Not enough beams (Mechanism)"
            return False
        return True

    def solve(self, point_load=None):
        self.results = {}
        n_nodes = len(self.nodes)
        if n_nodes < 2: return False

        node_map = {node: i for i, node in enumerate(self.nodes)}
        size = 2 * n_nodes
        K = [[0.0] * size for _ in range(size)]
        F_vec = [0.0] * size 

        # --- 1. Assemble Stiffness Matrix & Mass Calculation ---
        # Initialize Node Mass (for gravity load)
        node_masses = [0.0] * n_nodes

        for beam in self.beams:
            n1, n2 = node_map[beam.node_a], node_map[beam.node_b]
            dx = beam.node_b.x - beam.node_a.x
            dy = beam.node_b.y - beam.node_a.y
            L = math.sqrt(dx**2 + dy**2)
            if L == 0: continue

            # Get Properties (Includes Thickness Scaling)
            props = MaterialManager.get_properties(beam.type, beam.hollow)
            E = props["E"]
            lin_density = props["density"]

            # A. Stiffness (K)
            k = E / L
            cx, cy = dx / L, dy / L
            
            coeffs = [
                [ cx*cx,  cx*cy, -cx*cx, -cx*cy],
                [ cx*cy,  cy*cy, -cx*cy, -cy*cy],
                [-cx*cx, -cx*cy,  cx*cx,  cx*cy],
                [-cx*cy, -cy*cy,  cx*cy,  cy*cy]
            ]
            indices = [2*n1, 2*n1+1, 2*n2, 2*n2+1]
            
            for r in range(4):
                for c in range(4):
                    K[indices[r]][indices[c]] += k * coeffs[r][c]

            # B. Mass Distribution (Gravity Load)
            # Beam Mass = Linear Density * Length
            beam_mass = lin_density * L
            # Distribute half to each node
            node_masses[n1] += beam_mass / 2.0
            node_masses[n2] += beam_mass / 2.0

        # --- 2. Apply Loads ---
        # A. Dead Load (Gravity)
        for i in range(n_nodes):
            # F = m * g (downwards)
            F_vec[2*i + 1] -= node_masses[i] * 9.81 
        
        # B. Live Load (Ixchel)
        if point_load:
            agent_force = point_load['mass'] * 9.81
            
            n1_idx = node_map[point_load['node_a']]
            n2_idx = node_map[point_load['node_b']]
            t = point_load['t']
            
            F_vec[2*n1_idx + 1] -= agent_force * (1.0 - t)
            F_vec[2*n2_idx + 1] -= agent_force * t

        # C. Fixed Anchors
        for i, node in enumerate(self.nodes):
            if node.fixed:
                penalty = 1e15
                K[2*i][2*i] += penalty
                K[2*i+1][2*i+1] += penalty

        # --- 3. Solve ---
        try:
            displacements = self.gaussian_solve(K, F_vec)
        except ValueError:
            self.error_msg = "Singular Matrix: Structure is unstable!"
            return False

        # --- 4. Internal Forces ---
        for beam in self.beams:
            n1, n2 = node_map[beam.node_a], node_map[beam.node_b]
            u1, v1 = displacements[2*n1], displacements[2*n1+1]
            u2, v2 = displacements[2*n2], displacements[2*n2+1]
            
            dx = beam.node_b.x - beam.node_a.x
            dy = beam.node_b.y - beam.node_a.y
            L = math.sqrt(dx**2 + dy**2)
            
            cx, cy = dx/L, dy/L
            deformation = (u2 - u1)*cx + (v2 - v1)*cy
            
            props = MaterialManager.get_properties(beam.type, beam.hollow)
            force = (props["E"] / L) * deformation
            
            self.results[beam] = force
            
        return True

    def gaussian_solve(self, K, F):
        n = len(F)
        for i in range(n):
            pivot = K[i][i]
            if abs(pivot) < 1e-9: raise ValueError("Singular")
            for j in range(i + 1, n):
                factor = K[j][i] / pivot
                F[j] -= factor * F[i]
                for k in range(i, n):
                    K[j][k] -= factor * K[i][k]
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            sum_ax = sum(K[i][j] * x[j] for j in range(i + 1, n))
            x[i] = (F[i] - sum_ax) / K[i][i]
        return x