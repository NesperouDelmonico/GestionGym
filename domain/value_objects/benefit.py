class Benefit:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def __eq__(self, other):
        if not isinstance(other, Benefit):
            return False

        return (
            self.name == other.name
            and self.description == other.description
        )

    def __repr__(self):
        return f"Benefit(name='{self.name}')"
    