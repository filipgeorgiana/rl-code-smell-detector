class Heuristic:
    def __init__(self, name, details, line_nr, is_code_smell, category):
        self.name = name
        self.details = details
        self.line_nr = line_nr
        self.is_code_smell = is_code_smell
        self.category = category