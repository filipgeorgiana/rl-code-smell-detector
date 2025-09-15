import ast
import re

from model.category import Category
from model.heuristic import Heuristic

checkpoint_saving_pattern = r'\b(save|save_checkpoint|self\.saver|save_weights|model_save)\b'
lib_specific_checkpoint_saving_pattern = r'\b(torch\.save|pickle\.dump|joblib\.dump|model\.save)\b'

excluded_checkpoint_patterns = [
    r"img\.save",       # Exclude image saving
    r"temp/",           # Exclude temporary files
    r"env\.render",     # Exclude rendering
    r"env\.step",       # Exclude environment steps
]

final_save_patterns = [
    r"cfg\.save_model",
    r"cfg\.save_replay_buffer",
    r"upload_file_to_artifacts",
]

class CheckpointSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.checkpoint_saving_detected = False
        self.save_calls = []
        self.report = []
        self.in_loop = False

    def visit_For(self, node):
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = False

    def visit_While(self, node):
        self.in_loop = True
        self.generic_visit(node)
        self.in_loop = False

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        else:
            func_name = None

        if func_name and (re.search(checkpoint_saving_pattern, func_name) or re.search(lib_specific_checkpoint_saving_pattern, func_name)):
            self.is_checkpoint_saving(node)

        self.generic_visit(node)

    def is_checkpoint_saving(self, node):
        node_code = ast.unparse(node)
        if any(re.search(pattern, node_code) for pattern in excluded_checkpoint_patterns):
            return
        self.checkpoint_saving_detected = True
        self.save_calls.append(node_code)

    def get_report(self):
        if not self.checkpoint_saving_detected:
            self.report.append(Heuristic(
                "Missing checkpoint saving",
                "The model does not implement intermediate checkpoint saving. Training progress could be lost.",
                None,
                True,
                Category.TRAINING
            ))
        return self.report
