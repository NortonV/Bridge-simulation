import numpy as np
import math
from core.material_manager import MaterialManager

class StaticSolver:
    def __init__(self, bridge):
        self.bridge = bridge
        self.results = {}          
        self.bending_results = {}  
        self.stress_ratios = {}    
        self.displacements = {}    
        self.error_msg = ""

    def is_stable(self):
        fixed_nodes = sum(1 for n in self.bridge.nodes if n.fixed)
        if fixed_nodes < 2:
            self.error_msg = "Unstable: Need at least 2 anchors."
            return False
        return True

    def solve(self, temperature=0.0, point_load=None):
        nodes = self.bridge.nodes
        beams = self.bridge.beams
        n_nodes = len(nodes)
        
        if n_nodes < 2 or not beams:
            self.error_msg = "Empty structure"
            return False

        dof_map = {}
        for i, node in enumerate(nodes):
            dof_map[node] = (3*i, 3*i+1, 3*i+2)
            
        total_dofs = 3 * n_nodes
        K_global = np.zeros((total_dofs, total_dofs))
        F_global = np.zeros(total_dofs)
        
        # 2. Assemble Matrix
        for beam in beams:
            # Use global material properties (including hollow_ratio)
            props = MaterialManager.get_properties(beam.type)
            E = props["E"]
            A = props["area"]
            I = props["inertia"]
            
            n1, n2 = beam.node_a, beam.node_b
            dx = n2.x - n1.x
            dy = n2.y - n1.y
            L = math.sqrt(dx**2 + dy**2)
            if L < 0.001: continue 
            
            c = dx / L
            s = dy / L
            
            k_local = np.array([
                [ E*A/L,        0,             0,           -E*A/L,       0,             0           ],
                [ 0,            12*E*I/L**3,   6*E*I/L**2,  0,            -12*E*I/L**3,  6*E*I/L**2  ],
                [ 0,            6*E*I/L**2,    4*E*I/L,     0,            -6*E*I/L**2,   2*E*I/L     ],
                [ -E*A/L,       0,             0,           E*A/L,        0,             0           ],
                [ 0,            -12*E*I/L**3,  -6*E*I/L**2, 0,            12*E*I/L**3,   -6*E*I/L**2 ],
                [ 0,            6*E*I/L**2,    2*E*I/L,     0,            -6*E*I/L**2,   4*E*I/L     ]
            ])
            
            T = np.zeros((6, 6))
            block = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
            T[0:3, 0:3] = block
            T[3:6, 3:6] = block
            
            k_global = T.T @ k_local @ T
            
            idxs = dof_map[n1] + dof_map[n2]
            for i in range(6):
                for j in range(6):
                    K_global[idxs[i], idxs[j]] += k_global[i, j]

            # Gravity
            g = 9.81
            mass = props["density"] * A * L
            weight = mass * g
            w_total = weight / L
            w_axial = w_total * s      
            w_trans = -w_total * c     
            
            fea = np.array([
                -w_axial*L/2, w_trans*L/2, w_trans*L**2/12,
                -w_axial*L/2, w_trans*L/2, -w_trans*L**2/12
            ])
            
            fea_global = T.T @ fea
            for i in range(6):
                F_global[idxs[i]] += fea_global[i]

            # Thermal Load
            if abs(temperature) > 0.01:
                alpha = props["alpha"]
                # Force = E * A * alpha * delta_T
                thermal_force = E * A * alpha * temperature
                fx = thermal_force * c
                fy = thermal_force * s
                
                F_global[idxs[0]] -= fx
                F_global[idxs[1]] -= fy
                F_global[idxs[3]] += fx
                F_global[idxs[4]] += fy

            # Point Load
            if point_load and point_load['beam'] == beam:
                P_mag = point_load['mass'] * 9.81
                t = point_load['t']
                P_axial = P_mag * s
                P_trans = -P_mag * c
                
                a = t * L
                b = (1 - t) * L
                
                M1 = P_trans * a * (b**2) / (L**2)
                M2 = -P_trans * (a**2) * b / (L**2)
                V1 = (P_trans * b / L) + (M1 + M2) / L
                V2 = (P_trans * a / L) - (M1 + M2) / L
                N1 = -P_axial * (b / L)
                N2 = -P_axial * (a / L)
                
                pl_loc = np.array([N1, V1, M1, N2, V2, M2])
                pl_glob = T.T @ pl_loc
                for i in range(6):
                    F_global[idxs[i]] += pl_glob[i]

        free_dofs = []
        for i, node in enumerate(nodes):
            idxs = dof_map[node]
            if node.fixed:
                pass 
            else:
                free_dofs.extend(idxs)

        if not free_dofs:
            self.error_msg = "Fully constrained"
            return True

        K_reduced = K_global[np.ix_(free_dofs, free_dofs)]
        F_reduced = F_global[free_dofs]

        try:
            d_free = np.linalg.solve(K_reduced, F_reduced)
        except np.linalg.LinAlgError:
            self.error_msg = "Structure Unstable (Singular Matrix)"
            return False

        D_global = np.zeros(total_dofs)
        D_global[free_dofs] = d_free
        
        self.displacements.clear()
        for i, node in enumerate(nodes):
             idx = 3 * i
             self.displacements[node] = (D_global[idx], D_global[idx+1], D_global[idx+2])

        self.results.clear()
        self.bending_results.clear()
        self.stress_ratios.clear()
        
        for beam in beams:
            n1, n2 = beam.node_a, beam.node_b
            props = MaterialManager.get_properties(beam.type)
            
            idxs = dof_map[n1] + dof_map[n2]
            u_global = D_global[list(idxs)]
            
            dx = n2.x - n1.x
            dy = n2.y - n1.y
            L = math.sqrt(dx**2 + dy**2)
            c, s = dx/L, dy/L
            
            T = np.zeros((6, 6))
            block = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
            T[0:3, 0:3] = block
            T[3:6, 3:6] = block
            
            u_local = T @ u_global
            
            E, A, I = props["E"], props["area"], props["inertia"]
            k_local = np.array([
                [ E*A/L,        0,             0,           -E*A/L,       0,             0           ],
                [ 0,            12*E*I/L**3,   6*E*I/L**2,  0,            -12*E*I/L**3,  6*E*I/L**2  ],
                [ 0,            6*E*I/L**2,    4*E*I/L,     0,            -6*E*I/L**2,   2*E*I/L     ],
                [ -E*A/L,       0,             0,           E*A/L,        0,             0           ],
                [ 0,            -12*E*I/L**3,  -6*E*I/L**2, 0,            12*E*I/L**3,   -6*E*I/L**2 ],
                [ 0,            6*E*I/L**2,    2*E*I/L,     0,            -6*E*I/L**2,   4*E*I/L     ]
            ])
            
            f_local = k_local @ u_local
            
            axial_force = f_local[3] 
            max_moment = max(abs(f_local[2]), abs(f_local[5]))
            
            sigma_axial = abs(axial_force) / A
            sigma_bending = (max_moment * (props["thickness"] / 2.0)) / I
            
            total_stress = sigma_axial + sigma_bending
            stress_ratio = total_stress / props["strength"]
            
            bending_force_equiv = sigma_bending * A

            if axial_force < 0:
                P_cr = (math.pi**2 * E * I) / (L**2)
                if abs(axial_force) > P_cr:
                    stress_ratio = 999.0 
            
            self.results[beam] = axial_force
            self.bending_results[beam] = bending_force_equiv 
            self.stress_ratios[beam] = stress_ratio
            beam.stress = min(1.0, stress_ratio)

        return True