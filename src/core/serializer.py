import json
import os
import tkinter as tk
from tkinter import filedialog
from core.material_manager import MaterialManager
from entities.bridge import Node

class Serializer:
    @staticmethod
    def _get_saves_dir():
        base_path = os.getcwd()
        save_dir = os.path.join(base_path, "saves")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        return save_dir

    @staticmethod
    def save_as(bridge):
        root = tk.Tk()
        root.withdraw() 
        default_dir = Serializer._get_saves_dir()

        file_path = filedialog.asksaveasfilename(
            title="Save Bridge Design",
            initialdir=default_dir,
            defaultextension=".json",
            filetypes=[("Bridge Files", "*.json"), ("All Files", "*.*")]
        )
        root.destroy()
        
        if not file_path: return False, "Save Cancelled"
        return Serializer._write_to_file(bridge, file_path)

    @staticmethod
    def open_file(bridge):
        root = tk.Tk()
        root.withdraw()
        default_dir = Serializer._get_saves_dir()
        
        file_path = filedialog.askopenfilename(
            title="Load Bridge Design",
            initialdir=default_dir,
            filetypes=[("Bridge Files", "*.json"), ("All Files", "*.*")]
        )
        root.destroy()
        
        if not file_path: return False, "Load Cancelled"
        return Serializer._read_from_file(bridge, file_path)

    @staticmethod
    def _write_to_file(bridge, filename):
        data = {
            "version": 1.1,
            "materials": MaterialManager.MATERIALS,
            "settings": MaterialManager.SETTINGS,
            "nodes": [],
            "beams": []
        }
        
        node_to_index = {node: i for i, node in enumerate(bridge.nodes)}

        for n in bridge.nodes:
            data["nodes"].append({
                "x": n.x,
                "y": n.y,
                "fixed": n.fixed
            })

        for b in bridge.beams:
            idx_a = node_to_index[b.node_a]
            idx_b = node_to_index[b.node_b]
            data["beams"].append({
                "u": idx_a,
                "v": idx_b,
                "type": b.type,
                "hollow_ratio": b.hollow_ratio 
            })

        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
            name = os.path.basename(filename)
            return True, f"Saved: {name}"
        except Exception as e:
            return False, f"Save Error: {e}"

    @staticmethod
    def _read_from_file(bridge, filename):
        if not os.path.exists(filename):
            return False, "File not found!"

        try:
            with open(filename, "r") as f:
                data = json.load(f)

            # Load Settings if available
            if "materials" in data:
                for mat_key, mat_props in data["materials"].items():
                    if mat_key in MaterialManager.MATERIALS:
                        MaterialManager.MATERIALS[mat_key].update(mat_props)
            
            if "settings" in data:
                MaterialManager.SETTINGS.update(data["settings"])
            
            bridge.nodes.clear()
            bridge.beams.clear()

            created_nodes = []
            
            for n_data in data["nodes"]:
                new_node = Node(n_data["x"], n_data["y"], n_data["fixed"])
                bridge.nodes.append(new_node)
                created_nodes.append(new_node)

            for b_data in data["beams"]:
                idx_a = b_data["u"]
                idx_b = b_data["v"]
                mat_type = b_data["type"]

                if idx_a < len(created_nodes) and idx_b < len(created_nodes):
                    node_a = created_nodes[idx_a]
                    node_b = created_nodes[idx_b]
                    beam = bridge.add_beam_direct(node_a, node_b, mat_type)
                    # Load hollow ratio if exists
                    if "hollow_ratio" in b_data:
                        beam.hollow_ratio = b_data["hollow_ratio"]

            name = os.path.basename(filename)
            return True, f"Loaded: {name}"
        except Exception as e:
            return False, f"Load Error: {e}"