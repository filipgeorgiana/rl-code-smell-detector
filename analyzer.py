import ast

from detectors.agent_smells_detector import AgentSmellsDetector
from detectors.checkpoint_smells_detector import CheckpointSmellsDetector
from detectors.environment_smells_detector import EnvironmentSmellsDetector
from detectors.evaluation_smells_detector import EvaluationSmellsDetector
from detectors.hyperaparmeters_smells_detector import HyperparametersSmellsDetector
from detectors.initialization_smells_detector import InitializationSmellsDetector
from detectors.logging_detector import LoggingDetector
from detectors.training_smells_detector import TrainEvalCouplingDetector


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.environment_smells = EnvironmentSmellsDetector()
        self.checkpoint_smells = CheckpointSmellsDetector()
        self.hyperparameter_smells = HyperparametersSmellsDetector()
        self.evaluation_smells = EvaluationSmellsDetector()
        self.logging_smells = LoggingDetector()
        self.initialization_smells = InitializationSmellsDetector()
        self.agent_smells = AgentSmellsDetector()
        self.training_smells = TrainEvalCouplingDetector()
        self.report = []

    def visit_Assign(self, node):
        self.hyperparameter_smells.visit_Assign(node)
        self.evaluation_smells.visit_Assign(node)
        self.environment_smells.visit_Assign(node)
        self.initialization_smells.visit_Assign(node)
        self.generic_visit(node)

    def visit_Call(self, node):
        self.checkpoint_smells.visit_Call(node)
        self.hyperparameter_smells.visit_Call(node)
        self.evaluation_smells.visit_Call(node)
        self.environment_smells.visit_Call(node)
        self.logging_smells.visit_Call(node)
        self.agent_smells.visit_Call(node)
        self.training_smells.visit_Call(node)
        self.generic_visit(node)

    def visit_Import(self, node):
        self.logging_smells.visit_Import(node)
        self.hyperparameter_smells.visit_Import(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.logging_smells.visit_ImportFrom(node)
        self.hyperparameter_smells.visit_ImportFrom(node)
        self.generic_visit(node)

    def visit_Expr(self, node):
        self.environment_smells.visit_Expr(node)
        self.generic_visit(node)

    def visit_For(self, node):
        self.checkpoint_smells.visit_For(node)
        self.generic_visit(node)

    def visit_While(self, node):
        self.checkpoint_smells.visit_While(node)
        self.generic_visit(node)

    def visit_If(self, node):
        self.initialization_smells.visit_If(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.training_smells.visit_FunctionDef(node)
        self.generic_visit(node)

    def visit_arguments(self, node):
        self.training_smells.visit_arguments(node)
        self.generic_visit(node)

    def get_report(self):
        self.get_env_smells_report()
        self.get_checkpoint_smells_report()
        self.get_hyperparameter_smells_report()
        self.get_evaluation_smells_report()
        self.get_logging_smells_report()
        self.get_init_smells_report()
        self.get_agent_smells_report()
        self.get_training_smells_report()

        return self.report

    def get_training_smells_report(self):
        if self.training_smells.report:
            self.report.append(self.training_smells.report)

    def get_agent_smells_report(self):
        agent_smells_report = self.agent_smells.get_report()
        if agent_smells_report:
            self.report.append(agent_smells_report)

    def get_init_smells_report(self):
        initialization_report = self.initialization_smells.get_report()
        if initialization_report:
            self.report.append(initialization_report)

    def get_logging_smells_report(self):
        logging_report = self.logging_smells.get_report()
        if logging_report:
            self.report.append(logging_report)

    def get_evaluation_smells_report(self):
        evaluation_report = self.evaluation_smells.get_report()
        if evaluation_report:
            self.report.append(evaluation_report)

    def get_hyperparameter_smells_report(self):
        hyperparameter_report = self.hyperparameter_smells.generate_report()
        if hyperparameter_report:
            self.report.append(hyperparameter_report)

    def get_checkpoint_smells_report(self):
        checkpoint_report = self.checkpoint_smells.get_report()
        if checkpoint_report:
            self.report.append(checkpoint_report)

    def get_env_smells_report(self):
        env_smells_report = self.environment_smells.get_report()
        if env_smells_report:
            self.report.append(env_smells_report)