import ast
import re

from model.category import Category
from model.heuristic import Heuristic

evaluation_patterns = [
            r"^model\.eval$",          # PyTorch evaluation mode
            r"^model\.evaluate$",      # TensorFlow or Keras evaluation
            r"^test_env\.",            # Test environment usage
            r"^validation_env\."       # Validation environment usage
        ]

class EvaluationSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.training_loops = []
        self.evaluation_detected = False
        self.evaluation_calls = set()
        self.report = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            full_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"
            if any(re.fullmatch(pattern, full_name) for pattern in evaluation_patterns):
                self.evaluation_detected = True
                self.evaluation_calls.add((full_name, node.lineno))

        # for EvalCallback calls
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name == "EvalCallback":
                self.evaluation_detected = True
                self.evaluation_calls.add((func_name, node.lineno))

            elif any(re.fullmatch(pattern, func_name) for pattern in evaluation_patterns):
                self.evaluation_detected = True
                self.evaluation_calls.add((func_name, node.lineno))

        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                if func_name == "EvalCallback":
                    self.evaluation_detected = True
                    self.evaluation_calls.add((func_name, node.lineno))
                elif any(re.fullmatch(pattern, func_name) for pattern in evaluation_patterns):
                    self.evaluation_detected = True
                    self.evaluation_calls.add((func_name, node.lineno))

        self.generic_visit(node)

    def get_report(self):
        for call in self.evaluation_calls:
            self.report.append(Heuristic(
                "Model evaluation detected",
                f"Evaluation call '{call[0]}' detected at line {call[1]}",
                call[1],
                False,
                Category.EVALUATION
            ))
        if not self.evaluation_detected:
            self.report.append(Heuristic(
                "Missing model evaluation",
                f"Evaluation call not found in the script",
                None,
                True,
                Category.EVALUATION
            ))
        return self.report