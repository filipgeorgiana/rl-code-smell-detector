import ast
import re

from model.category import Category
from model.heuristic import Heuristic
# this class detect ambiguous initialization for multi agents
# todo move to agent smells detector

class InitializationSmellsDetector(ast.NodeVisitor):
    def __init__(self):
        self.ambiguous_flags = set()
        self.agent_count_vars = set()
        self.conditional_checks = set()
        self.report = []

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id

            if re.search(r"(multi_agent|ma|multi|shared)", var_name, re.IGNORECASE):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, bool):
                    self.ambiguous_flags.add((var_name, node.value.value))

            if re.search(r"(agents|num_agents|n_agents|players)", var_name, re.IGNORECASE):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                    self.agent_count_vars.add((var_name, node.value.value, node.lineno))

        self.generic_visit(node)

    def visit_If(self, node):
        condition_code = ast.unparse(node.test)
        if any(flag in condition_code for flag, _ in self.ambiguous_flags):
            self.conditional_checks.add(condition_code)

        self.generic_visit(node)

    def get_report(self):
        if self.ambiguous_flags and self.agent_count_vars:
            for agent_init in self.agent_count_vars:
                self.report.append(Heuristic(
                    "Ambiguous initialization for Multi Agent",
                    f"Possible design smell: ambiguous initialization {agent_init[0]}={agent_init[1]} and {self.ambiguous_flags}",
                    agent_init[2], False, Category.AGENT))
        return self.report


