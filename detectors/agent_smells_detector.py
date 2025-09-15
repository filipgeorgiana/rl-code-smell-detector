import ast
import re

from model.category import Category
from model.heuristic import Heuristic

random_patterns = [
    r"random\.choice",
    r"random\.rand.*",
    r"np\.random\..*",
]

policy_functions = {"predict", "act", "choose_action", "select_action"}

class AgentSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.action_space_sample_calls = set()
        self.empty_action_dicts = set()
        self.policy_based_calls = set()
        self.random_action_calls = []
        self.report = []

    def visit_Call(self, node):
        call_code = ast.unparse(node)

        if isinstance(node.func, ast.Attribute) and node.func.attr == "sample":
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "action_space":
                self.action_space_sample_calls.add((call_code, node.lineno))

        if isinstance(node.func, ast.Attribute) and node.func.attr == "step":
            if node.args and isinstance(node.args[0], ast.Dict) and len(node.args[0].keys) == 0:
                self.empty_action_dicts.add((call_code, node.lineno))

        if isinstance(node.func, ast.Attribute) and node.func.attr in policy_functions:
            self.policy_based_calls.add((call_code, node.lineno))

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        for func in node.body:
            if isinstance(func, ast.FunctionDef) and func.name == "act":
                for statement in func.body:
                    if isinstance(statement, ast.Return):
                        if isinstance(statement.value, ast.Call):
                            if isinstance(statement.value.func, ast.Attribute):
                                function_call = ast.unparse(statement.value.func)
                                if re.search(r"\.sample\(\)$", function_call):
                                    self.random_action_calls.append({
                                        "class": node.name,
                                        "method": func.name,
                                        "line": statement.lineno,
                                        "call": function_call
                                    })
                                    self.report.append(
                                        Heuristic(
                                            "Random action selection",
                                            f"{node.name} has a random action selection {function_call}",
                                            statement.lineno,
                                            True,
                                            Category.AGENT
                                        ))

        self.generic_visit(node)

    def get_report(self):
        if (self.action_space_sample_calls or self.empty_action_dicts) and not self.policy_based_calls:
            for call in self.action_space_sample_calls:
                self.report.append(
                    Heuristic(
                        "Random behavior detected for sampling",
                        f"{call[0]}",
                        call[1] ,
                        True,
                        Category.AGENT
                    ))
            for call in self.empty_action_dicts:
                self.report.append(
                    Heuristic(
                        "Random behavior detected for actions",
                        f"{call[0]}",
                        call[1] ,
                        True,
                        Category.AGENT
                    ))
        return self.report
