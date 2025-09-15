from typing import List

from model.heuristic import Heuristic

class Report:
    def __init__(self, filename, heuristics: List[Heuristic]):
        self.filename = filename
        self.heuristics = heuristics