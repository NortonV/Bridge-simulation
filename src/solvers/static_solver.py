import numpy as np
import math
from core.material_manager import MaterialManager
from core.constants import *

class StaticSolver:
    def __init__(self, bridge):
        self.bridge = bridge
        self.results = {} 
        self.bending_results = {}
        self.stress_ratios = {} 
        self.displacements = {}
        self.error_msg = "OK"

    def is_stable(self):
        return True 

    def solve(self, temperature=0.0, point_load=None):
        self.results.clear()
        self.stress_ratios.clear()
        self.displacements.clear()
        
        # 1. Degrees of Freedom
        nodes = self.bridge.nodes
        beams = self.bridge.beams
        n_nodes = len(nodes)
        
        node_map = {node: i for i, node in enumerate(nodes)}
        dof = 3 * n_nodes
        
        K_global = np.zeros((dof, dof))
        F_global = np.zeros(dof)

        # Dictionary to store Fixed End Moments (FEM) for post-processing stress
        # Key: beam, Value: (Moment_at_A, Moment_at_B)
        beam_fem_loads = {}

        # 2. Build Stiffness Matrix
        for beam in beams:
            i = node_map[beam.node_a]
            j = node_map[beam.node_b]
            
            props = MaterialManager.get_properties(beam.type, hollow_ratio=beam.hollow_ratio)
            
            E = props["E"]
            A = props["area"]
            I = props["inertia"]
            
            dx = beam.node_b.x - beam.node_a.x
            dy = beam.node_b.y - beam.node_a.y
            L = math.sqrt(dx*dx + dy*dy)
            
            c = dx / L
            s = dy / L
            
            # Local Stiffness (Frame element)
            k_local = np.array([
                [A*E/L, 0, 0, -A*E/L, 0, 0],
                [0, 12*E*I/L**3, 6*E*I/L**2, 0, -12*E*I/L**3, 6*E*I/L**2],
                [0, 6*E*I/L**2, 4*E*I/L, 0, -6*E*I/L**2, 2*E*I/L],
                [-A*E/L, 0, 0, A*E/L, 0, 0],
                [0, -12*E*I/L**3, -6*E*I/L**2, 0, 12*E*I/L**3, -6*E*I/L**2],
                [0, 6*E*I/L**2, 2*E*I/L, 0, -6*E*I/L**2, 4*E*I/L]
            ])
            
            # Rotation Matrix
            T = np.zeros((6, 6))
            T[0,0] = c;  T[0,1] = s
            T[1,0] = -s; T[1,1] = c
            T[2,2] = 1
            T[3,3] = c;  T[3,4] = s
            T[4,3] = -s; T[4,4] = c
            T[5,5] = 1
            
            k_global_beam = T.T @ k_local @ T
            
            indices = [3*i, 3*i+1, 3*i+2, 3*j, 3*j+1, 3*j+2]
            for r in range(6):
                for c_idx in range(6):
                    K_global[indices[r], indices[c_idx]] += k_global_beam[r, c_idx]

            # Thermal Load
            alpha = props["alpha"]
            if temperature != 0:
                therm_strain = alpha * temperature
                f_therm = -E * A * therm_strain
                
                f_local_therm = np.array([-f_therm, 0, 0, f_therm, 0, 0])
                f_global_therm = T.T @ f_local_therm
                
                for idx_k, global_idx in enumerate(indices):
                    F_global[global_idx] -= f_global_therm[idx_k]

        # 3. Loads (Gravity + Custom)
        g = 9.81
        for beam in beams:
            props = MaterialManager.get_properties(beam.type, hollow_ratio=beam.hollow_ratio)
            mass = props["area"] * beam.length * props["density"]
            weight = mass * g
            
            # FIX 1: SUBTRACT weight (Gravity acts DOWN, Y is UP)
            idx_a_y = node_map[beam.node_a] * 3 + 1
            idx_b_y = node_map[beam.node_b] * 3 + 1
            F_global[idx_a_y] -= weight / 2.0
            F_global[idx_b_y] -= weight / 2.0
        
        # Point Load (Agent)
        if point_load:
            # {beam: (t, mass)}
            for beam, (t, mass) in point_load.items():
                P = mass * g
                L = beam.length
                
                # Parameters for position
                a = t * L
                b = (1.0 - t) * L
                
                # --- FIX 2: Fixed End Moments & Reaction Forces ---
                # Instead of simple linear interpolation, we use exact beam formulas.
                # This ensures that even if nodes are FIXED, the load is registered as moments.
                
                # Vertical Reaction Forces (Standard Fixed-Fixed Beam formulas)
                # These act UP on the beam, so equivalent nodal loads act DOWN (-)
                R_a = (P * b**2 * (3*a + b)) / L**3
                R_b = (P * a**2 * (a + 3*b)) / L**3
                
                # Fixed End Moments (Standard formulas)
                # Load P is Down.
                # Reaction at A is CCW (+). Equivalent Load on Node A is CW (-).
                # Reaction at B is CW (-). Equivalent Load on Node B is CCW (+).
                M_a = (P * a * b**2) / L**2
                M_b = (P * a**2 * b) / L**2
                
                # Apply to Global Force Vector (Signs inverted for Equivalent Nodal Loads)
                idx_a = node_map[beam.node_a] * 3
                idx_b = node_map[beam.node_b] * 3
                
                # Vertical Load (Y-axis is index +1)
                F_global[idx_a + 1] -= R_a
                F_global[idx_b + 1] -= R_b
                
                # Moment Load (Theta-axis is index +2)
                # Reaction A is CCW (+), so Eq Load is CW (-)
                F_global[idx_a + 2] -= M_a 
                # Reaction B is CW (-), so Eq Load is CCW (+)
                F_global[idx_b + 2] += M_b 
                
                # Store these FEMs to add them back during stress calculation
                # (Superposition: Total Moment = Moment_from_Nodes + Moment_Fixed_End)
                beam_fem_loads[beam] = (M_a, -M_b) # Store as Internal Moments (Reaction direction)

        # 4. Boundary Conditions
        fixed_dofs = []
        for i, node in enumerate(nodes):
            if node.fixed:
                fixed_dofs.extend([3*i, 3*i+1, 3*i+2])
        
        free_dofs = [x for x in range(dof) if x not in fixed_dofs]
        
        K_reduced = K_global[np.ix_(free_dofs, free_dofs)]
        F_reduced = F_global[free_dofs]
        
        # 5. Solve
        try:
            U_reduced = np.linalg.solve(K_reduced, F_reduced)
        except np.linalg.LinAlgError:
            self.error_msg = "Instabil: Szinguláris Mátrix"
            return False 
        
        U_global = np.zeros(dof)
        U_global[free_dofs] = U_reduced
        
        # --- POST PROCESSING ---
        for i, node in enumerate(nodes):
            self.displacements[node] = (U_global[3*i], U_global[3*i+1], U_global[3*i+2])

        for beam in beams:
            i = node_map[beam.node_a]
            j = node_map[beam.node_b]
            
            u_elem = np.concatenate((U_global[3*i:3*i+3], U_global[3*j:3*j+3]))
            
            dx = beam.node_b.x - beam.node_a.x
            dy = beam.node_b.y - beam.node_a.y
            L = math.sqrt(dx*dx + dy*dy)
            c = dx/L; s = dy/L
            
            props = MaterialManager.get_properties(beam.type, hollow_ratio=beam.hollow_ratio)
            E = props["E"]
            A = props["area"]
            I = props["inertia"]

            # Local displacements
            T = np.zeros((6, 6))
            T[0,0] = c;  T[0,1] = s
            T[1,0] = -s; T[1,1] = c
            T[2,2] = 1
            T[3,3] = c;  T[3,4] = s
            T[4,3] = -s; T[4,4] = c
            T[5,5] = 1
            
            u_local = T @ u_elem
            
            # Axial Force (N = AE/L * delta_u_x)
            axial_strain = (u_local[3] - u_local[0]) / L
            therm_strain = props["alpha"] * temperature
            mech_strain = axial_strain - therm_strain
            axial_force = E * A * mech_strain
            
            # Bending Moment (Slope Deflection Equations)
            # M_ab = 2EI/L * (2*theta_a + theta_b - 3*psi)
            theta_a = u_local[2]
            theta_b = u_local[5]
            relative_disp = (u_local[4] - u_local[1]) / L # psi
            
            moment_a = (2*E*I/L) * (2*theta_a + theta_b - 3*relative_disp)
            moment_b = (2*E*I/L) * (2*theta_b + theta_a - 3*relative_disp)
            
            # --- FIX 3: Superposition of Fixed End Moments ---
            # If there is a point load, we must add the "Local" moments to the "Nodal" moments.
            # Otherwise, a fixed-fixed beam shows 0 stress.
            if beam in beam_fem_loads:
                fem_a, fem_b = beam_fem_loads[beam]
                moment_a += fem_a
                moment_b += fem_b

            max_moment = max(abs(moment_a), abs(moment_b))
            
            # 1. Calculate Standard Stress (Yield/Strength based)
            sigma_axial = axial_force / A
            sigma_bend = max_moment * (props["thickness"]/2) / I
            
            total_stress = abs(sigma_axial) + abs(sigma_bend)
            
            # Base ratio based on material strength
            stress_ratio_yield = total_stress / props["strength"]
            
            # Initialize final ratio
            final_stress_ratio = stress_ratio_yield

            # 2. Calculate Buckling Ratio (Stability based)
            if axial_force < 0: # Compression
                K = 1.0 
                # Euler Buckling Formula: P_cr = (pi^2 * E * I) / (K * L)^2
                P_cr = (math.pi**2 * E * I) / ((K*L)**2)
                
                # Calculate how close we are to buckling (0.0 to 1.0+)
                buckling_ratio = abs(axial_force) / P_cr
                
                # The beam is under load from whichever factor is higher
                final_stress_ratio = max(stress_ratio_yield, buckling_ratio)
                
                # Optional: Keep your instant failure flag if it exceeds 100%
                if buckling_ratio > 1.0:
                    final_stress_ratio = 1.0 

            # Store the result
            self.results[beam] = axial_force
            self.bending_results[beam] = max_moment 
            self.stress_ratios[beam] = final_stress_ratio # Use the corrected ratio

        return True