import ast

from model.category import Category
from model.heuristic import Heuristic


class TrainEvalCouplingDetector(ast.NodeVisitor):
    def __init__(self):
        self.train_func = None
        self.eval_func = None
        self.train_calls_eval = False
        self.train_uses_eval_env = False
        self.eval_callback_used = False
        self.report = []

    def visit_FunctionDef(self, node):
        if node.name == "train":
            self.train_func = node
        elif node.name == "evaluate":
            self.eval_func = node
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == "evaluate" and self.train_func and node in ast.walk(self.train_func):
                self.train_calls_eval = True
                self.report.append(
                    Heuristic(
                    "Training and evaluation coupling",
                    "Training function calls 'evaluate()'",
                    node.lineno,
                    True,
                    Category.TRAINING
                ))

            if node.func.id == "EvalCallback" and self.train_func and node in ast.walk(self.train_func):
                self.eval_callback_used = True
                self.report.append(
                    Heuristic(
                        "Training and evaluation coupling",
                        "'EvalCallback' is used inside training",
                        node.lineno,
                        True,
                        Category.TRAINING
                    ))

        self.generic_visit(node)

    def visit_arguments(self, node):
        if self.train_func and node in ast.walk(self.train_func):
            for arg in node.args:
                if arg.arg in ["envs_eval", "eval_env", "evaluation_envs"]:
                    self.train_uses_eval_env = True
                    self.report.append(Heuristic(
                        "Training and evaluation coupling",
                        f"Training function takes evaluation environments as argument: '{arg.arg}'",
                        self.train_func.lineno,
                        True,
                        Category.TRAINING
                    ))

        self.generic_visit(node)