import ast
import re

class RLScriptDetector(ast.NodeVisitor):
    def __init__(self):
        self.rl_imports = set()
        self.environments = set()
        self.models = set()
        self.agent_interactions = set()
        self.custom_envs = set()
        self.class_definitions = set()
        self.assignments = {}

        self.rl_libraries = {
            "gym", "stable_baselines3", "sb3_contrib", "ray.rllib", "rlberry", "torchrl"
        }

        self.rl_algorithms = {
            "PPO", "DQN", "A2C", "SAC", "TD3", "DDPG", "TRPO"
        }

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.rl_libraries:
                self.rl_imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and any(lib in node.module for lib in self.rl_libraries):
            self.rl_imports.add(node.module)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id

                if func_name in self.rl_algorithms:
                    self.models.add(var_name)

                if "env" in var_name.lower() or "Env" in func_name:
                    self.environments.add(var_name)

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if "Env" in node.name:
            self.class_definitions.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            func_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"

            self.detect_environment_creation(func_name)
            self.detect_model(func_name)
            self.detect_agent_interactions(func_name)

        elif isinstance(node.func, ast.Name):
            self.detect_custom_environment_creation(node)

        self.generic_visit(node)

    def detect_custom_environment_creation(self, node):
        if re.match(r"^(create_env|make_env)$", node.func.id):
            self.custom_envs.add(node.func.id)

    def detect_agent_interactions(self, func_name):
        if re.match(r".*\.(step|predict|learn|train)$", func_name):
            self.agent_interactions.add(func_name)

    def detect_model(self, func_name):
        if any(alg in func_name for alg in self.rl_algorithms):
            self.models.add(func_name)

    def detect_environment_creation(self, func_name):
        if re.match(r"^(gym|sumo_rl|custom_envs)\..*(make|create|Env)$", func_name):
            self.environments.add(func_name)

    # todo maybe refactor this and don't read the file twice
    def analyze(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filename)

        self.visit(tree)

        is_rl_script = bool(
            (self.rl_imports or self.models or self.agent_interactions)
            and (self.environments or self.custom_envs or self.class_definitions)
        )

        return is_rl_script
