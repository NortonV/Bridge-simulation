import json
import os
import tkinter as tk
from tkinter import filedialog

class Serializer:
    @staticmethod
    def _get_saves_dir():
        """ Helper to get (and create) the default saves directory. """
        # Get the directory where main.py is running
        base_path = os.getcwd()
        # Create path to 'saves' folder
        save_dir = os.path.join(base_path, "saves")
        
        # If it doesn't exist, create it
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        return save_dir

    @staticmethod
    def save_as(bridge):
        """ Opens a native OS file dialog to save the bridge. """
        root = tk.Tk()
        root.withdraw() 
        
        # Get the default directory
        default_dir = Serializer._get_saves_dir()

        file_path = filedialog.asksaveasfilename(
            title="Save Bridge Design",
            initialdir=default_dir, # <--- Starts in 'saves' folder
            defaultextension=".json",
            filetypes=[("Bridge Files", "*.json"), ("All Files", "*.*")]
        )
        
        root.destroy()
        
        if not file_path:
            return False, "Save Cancelled"
            
        return Serializer._write_to_file(bridge, file_path)

    @staticmethod
    def open_file(bridge):
        """ Opens a native OS file dialog to load a bridge. """
        root = tk.Tk()
        root.withdraw()
        
        # Get the default directory
        default_dir = Serializer._get_saves_dir()
        
        file_path = filedialog.askopenfilename(
            title="Load Bridge Design",
            initialdir=default_dir, # <--- Starts in 'saves' folder
            filetypes=[("Bridge Files", "*.json"), ("All Files", "*.*")]
        )
        
        root.destroy()
        
        if not file_path:
            return False, "Load Cancelled"
            
        return Serializer._read_from_file(bridge, file_path)

    @staticmethod
    def _write_to_file(bridge, filename):
        data = {
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
                "type": b.type
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

            bridge.nodes.clear()
            bridge.beams.clear()

            created_nodes = []
            from entities.bridge import Node
            
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
                    bridge.add_beam(node_a, node_b, mat_type)

            name = os.path.basename(filename)
            return True, f"Loaded: {name}"
        except Exception as e:
            return False, f"Load Error: {e}"