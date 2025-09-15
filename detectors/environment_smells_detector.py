import ast

from model.category import Category
from model.heuristic import Heuristic

class EnvironmentSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.report = []
        self.env_closed = False
        self.env_variable_names = ["env", "test.env"]
        self.env_assignments = {}
        self.video_recorders = set()

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            func_name = None
            if isinstance(node.value.func, ast.Name):  # DummyVecEnv()
                func_name = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):  # gym.make()
                func_name = node.value.func.attr

            if func_name and ("env" in func_name.lower() or "make" in func_name.lower()):
                if isinstance(node.targets[0], ast.Name):
                    env_var = node.targets[0].id
                    self.env_assignments[env_var] = node.lineno

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "VecVideoRecorder":
            if node.args:
                wrapped_env = node.args[0]

                if isinstance(wrapped_env, ast.Name):
                    env_name = wrapped_env.id
                    if env_name in self.env_assignments:
                        self.video_recorders.add((env_name, node.lineno, self.env_assignments[env_name]))

        self.generic_visit(node)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and hasattr(node.value.func, 'attr'):
            if node.value.func.attr == "close":
                if isinstance(node.value.func.value, ast.Name) and node.value.func.value.id in self.env_variable_names:
                    self.env_closed = True
                    self.report.append(
                        Heuristic(
                            "Environment Closed Detected",
                            node.value.func.value.id,
                            node.lineno,
                            False,
                            Category.ENVIRONMENT
                        ))

    def get_report(self):
        if self.video_recorders:
            for env_name, recorder_line, creation_line in self.video_recorders:
                self.report.append(
                    Heuristic(
                        "Redundant env creation",
                        f"Environment '{env_name}' created at line {creation_line} "
                        f"but another instance is used just for video recording at line {recorder_line}. ",
                        recorder_line,
                        True,
                        Category.ENVIRONMENT
                    )
                )
        return self.report