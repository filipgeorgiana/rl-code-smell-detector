import ast
import re

from model.category import Category
from model.heuristic import Heuristic


hyperparameter_patterns = [
            r"learning_rate", r"lr", r"gamma", r"discount_factor",
            r"epsilon", r"exploration_rate", r"target_update_interval",
            r"reward_threshold", r"max_steps", r"batch_size", r"reward_fn", r"discount", r"weight_decay", r"lr_init", r"lr_decay_rate", r"lr_decay_steps"
        ]

tuning_library_patterns = [
    r"optuna", r"ray\.tune", r"sklearn\.model_selection", r"hyperopt", r"bayes_opt"
]

tuning_function_patterns = [
    r"^optuna\.create_study$",                          # Matches optuna.create_study
    r"^optuna\.optimize$",                              # Matches optuna.optimize
    r"^ray\.tune\.run$",                                # Matches ray.tune.run
    r"^tune\.run$",                                     # Matches tune.run
    r"^sklearn\.model_selection\.GridSearchCV$",        # Matches sklearn.model_selection.GridSearchCV
    r"^model_selection\.GridSearchCV$",                 # Matches model_selection.GridSearchCV
    r"^sklearn\.model_selection\.RandomizedSearchCV$",  # Matches sklearn.model_selection.RandomizedSearchCV
    r"^model_selection\.RandomizedSearchCV$",           # Matches model_selection.RandomizedSearchCV
    r"^hyperopt\.fmin$",                                # Matches hyperopt.fmin
    r"^bayes_opt\.\w+$"                                 # Matches any function in bayes_opt
]

class HyperparametersSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.hardcoded_hyperparams = []
        self.hyperparameter_tuning = False
        self.found_tuning_imports = []
        self.found_tuning_usage = []
        self.report =[]

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                if any(re.search(pattern, target.id) for pattern in hyperparameter_patterns):
                    self.hardcoded_hyperparams.append((target.id, node.value.value, node.lineno))
            elif isinstance(target, ast.Attribute) and isinstance(node.value, ast.Constant):
                if any(re.search(pattern, target.attr) for pattern in hyperparameter_patterns):
                    self.hardcoded_hyperparams.append((target.attr, node.value.value, node.lineno))

    def visit_Import(self, node):
        for alias in node.names:
            if any(re.search(pattern, alias.name) for pattern in tuning_library_patterns):
                self.found_tuning_imports.append(alias.name)
                self.report.append(
                    Heuristic(
                        "Tuning",
                        f"Imported tuning library '{alias.name}' at line {node.lineno}",
                        node.lineno,
                        False,
                    Category.HYPERPARAMETER))

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if any(re.search(pattern, node.module or "") for pattern in tuning_library_patterns):
            self.found_tuning_imports.append(node.module)
            self.report.append(Heuristic(
                "Tuning",
                f"Imported from tuning library '{node.module}' at line {node.lineno}",
                node.lineno, False,
                Category.HYPERPARAMETER))

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            func_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"
            if any(re.search(pattern, func_name) for pattern in tuning_function_patterns):
                self.found_tuning_usage.append(func_name)
                self.report.append(Heuristic(
                    "Tuning",
                    f"Tuning function '{func_name}' used at line {node.lineno}",
                    node.lineno, False,
                    Category.HYPERPARAMETER))

        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if any(re.search(pattern, func_name) for pattern in tuning_function_patterns):
                self.found_tuning_usage.append(func_name)
                self.report.append(Heuristic(
                    "Tuning",
                    f"Tuning function '{func_name}' used at line {node.lineno}",
                    node.lineno, False,
                    Category.HYPERPARAMETER))
        self.generic_visit(node)

    def generate_report(self):
        if self.hardcoded_hyperparams:
            for param, value, line_number in self.hardcoded_hyperparams:
                self.report.append(Heuristic(
                    "Hardcoded hyperparameter",
                    f"{param}={value}",
                    line_number,
                    True,
                    Category.HYPERPARAMETER))
        if not self.found_tuning_imports and  not self.found_tuning_usage:
            self.report.append(Heuristic(
                "No tuning of hyperparameters",
                "hyperparameter tuning is missing from the script",
                None,
                True,
                Category.HYPERPARAMETER))
        return self.report
