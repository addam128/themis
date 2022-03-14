
class AssignmentSolverException(Exception):
    def __init__(self):
        super().__init__("Could not solve assignment for branches.")
