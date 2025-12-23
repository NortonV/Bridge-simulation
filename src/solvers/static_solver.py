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
        
        self.slack_vines = set()

    def is_stable(self):
        return True 

    def solve(self, temperature=0.0, point_load=None):
        self.results.clear()
        self.stress_ratios.clear()
        self.displacements.clear()
        self.slack_vines.clear()
        
        # Iterative solver to handle slack vines/cables (tension-only)
        max_iter = 10
        for iteration in range(max_iter):
            # 1. Degrees of Freedom
            nodes = self.bridge.nodes
            beams = self.bridge.beams
            n_nodes = len(nodes)
            
            node_map = {node: i for i, node in enumerate(nodes)}
            dof = 3 * n_nodes
            
            K_global = np.zeros((dof, dof))
            F_global = np.zeros(dof)

            # 2. Build Stiffness Matrix
            for beam in beams:
                i = node_map[beam.node_a]
                j = node_map[beam.node_b]
                
                props = MaterialManager.get_properties(beam.type)
                
                # Retrieve individual hollow ratio if available
                mat_settings = MaterialManager.MATERIALS.get(beam.type, {})
                # Note: In a full implementation, we would store hollow_ratio on the beam instance
                # For now, we rely on the material manager default
                
                E = props["E"]
                A = props["area"]
                I = props["inertia"]
                
                # If tension-only member is in slack set, reduce stiffness to near zero
                if beam.type in ["vine", "cable"] and beam in self.slack_vines:
                    E = E * 1e-6 
                
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
                    
                    # Local force vector for thermal expansion (Axial only)
                    f_local_therm = np.array([-f_therm, 0, 0, f_therm, 0, 0])
                    f_global_therm = T.T @ f_local_therm
                    
                    for idx_k, global_idx in enumerate(indices):
                        F_global[global_idx] -= f_global_therm[idx_k]

            # 3. Loads (Gravity + Custom)
            g = 9.81
            for beam in beams:
                props = MaterialManager.get_properties(beam.type)
                mass = props["area"] * beam.length * props["density"]
                weight = mass * g
                
                # Split weight to nodes
                idx_a = node_map[beam.node_a] * 3 + 1
                idx_b = node_map[beam.node_b] * 3 + 1
                F_global[idx_a] += weight / 2.0
                F_global[idx_b] += weight / 2.0
            
            # Point Load (Agent)
            if point_load:
                # {beam: (t, mass)}
                for beam, (t, mass) in point_load.items():
                    weight = mass * g
                    
                    # Distributed load based on 't'
                    # Simple linear interpolation for nodal loads
                    fa = weight * (1.0 - t)
                    fb = weight * t
                    
                    idx_a = node_map[beam.node_a] * 3 + 1
                    idx_b = node_map[beam.node_b] * 3 + 1
                    F_global[idx_a] += fa
                    F_global[idx_b] += fb

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
                return False 
            
            U_global = np.zeros(dof)
            U_global[free_dofs] = U_reduced
            
            # 6. Check for Slack Vines / Cables
            new_slack_vines = set()
            slack_change = False
            
            for beam in beams:
                if beam.type not in ["vine", "cable"]: continue
                
                i = node_map[beam.node_a]
                j = node_map[beam.node_b]
                
                ua = U_global[3*i:3*i+2]
                ub = U_global[3*j:3*j+2]
                
                dx = beam.node_b.x - beam.node_a.x
                dy = beam.node_b.y - beam.node_a.y
                L = math.sqrt(dx*dx + dy*dy)
                
                # Calculate change in length (projection of displacement onto axis)
                delta_l = ((ub[0]-ua[0])*dx + (ub[1]-ua[1])*dy) / L
                
                # Thermal effect
                props = MaterialManager.get_properties(beam.type)
                therm_delta = props["alpha"] * temperature * L
                
                # Net elongation
                net_elongation = delta_l - therm_delta
                
                # If shortened (compressed), it goes slack
                if net_elongation < -1e-9:
                    new_slack_vines.add(beam)
            
            if new_slack_vines != self.slack_vines:
                self.slack_vines = new_slack_vines
                slack_change = True
            
            if not slack_change:
                break # Converged

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
            
            props = MaterialManager.get_properties(beam.type)
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
            
            # Thermal correction for stress
            therm_strain = props["alpha"] * temperature
            mech_strain = axial_strain - therm_strain
            
            axial_force = E * A * mech_strain
            
            if beam in self.slack_vines:
                axial_force = 0.0

            # Bending Moment (Simplified max moment)
            # M = 6EI/L^2 * (uy_a - uy_b) ... roughly
            # Not fully accurate for frame, but good for vis
            # Detailed: M_a = 2EI/L (2theta_a + theta_b - 3(uy_b-uy_a)/L)
            
            theta_a = u_local[2]
            theta_b = u_local[5]
            relative_disp = (u_local[4] - u_local[1]) / L
            
            moment_a = (2*E*I/L) * (2*theta_a + theta_b - 3*relative_disp)
            moment_b = (2*E*I/L) * (2*theta_b + theta_a - 3*relative_disp)
            max_moment = max(abs(moment_a), abs(moment_b))
            
            # Stress Calc
            # sigma = F/A + M*y/I
            sigma_axial = axial_force / A
            sigma_bend = max_moment * (props["thickness"]/2) / I
            
            total_stress = abs(sigma_axial) + abs(sigma_bend)
            
            stress_ratio = total_stress / props["strength"]
            
            # Buckling Check for Compression (Euler)
            # Only for non-cables
            if axial_force < 0 and beam.type not in ["vine", "cable"]:
                K = 1.0 # Effective length factor
                P_cr = (math.pi**2 * E * I) / ((K*L)**2)
                if abs(axial_force) > P_cr:
                    stress_ratio = 999.0 # Instant fail
            
            self.results[beam] = axial_force
            self.bending_results[beam] = max_moment # Store moment force equivalent for simpler vis
            self.stress_ratios[beam] = stress_ratio

        return True