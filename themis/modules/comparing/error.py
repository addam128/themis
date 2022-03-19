
class AssignmentSolverException(Exception):
    def __init__(
        self
    ) -> None:
    
        super().__init__("Could not solve assignment for branches.")
