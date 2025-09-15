import ast

from model.category import Category
from model.heuristic import Heuristic

logging_libraries = {
    "logging", "loguru", "stable_baselines3.common.logger", "ray.tune.logger"
}

logging_methods = {
            "info", "debug", "error", "warning", "critical", "log"
        }

class LoggingDetector(ast.NodeVisitor):
    def __init__(self):
        self.logging_imports = set()
        self.logger_initialization = set()
        self.logging_calls = set()
        self.logging_detected = False
        self.report = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in logging_libraries:
                self.logging_imports.add(alias.name)
                self.report.append(
                    Heuristic(
                        "Logging",
                        f"logging library imported {alias.name}",
                        node.lineno,
                        False,
                        Category.CODESTYLE
                    ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module in logging_libraries:
            self.logging_imports.add(node.module)
            self.report.append(
                Heuristic(
                    "Logging",
                    f"logging library imported {node.module}",
                    node.lineno,
                    False,
                    Category.CODESTYLE
                ))

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if method_name in logging_methods:
                func_name = f"{ast.unparse(node.func.value)}.{method_name}"
                self.logging_calls.add(func_name)
                self.report.append(
                    Heuristic(
                        "Logging",
                        f"call {func_name}",
                        node.lineno,
                        False,
                        Category.CODESTYLE
                    ))
                self.logging_detected = True
        self.generic_visit(node)

    def get_report(self):
        if not self.logging_detected:
            self.report.append(
                Heuristic(
                    "Logging",
                    "No logging detected",
                    None,
                    True,
                    Category.CODESTYLE
                ))
        return self.report
