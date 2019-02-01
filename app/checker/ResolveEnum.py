import enum

class ResolveEnum(enum.Enum):
    """
    This class is an enumerator dictating how a checker compound
    should be handled during insertion, either from a checker problem
    or to facilitate updating a compounds information
    """
    new = 1
    replace = 2
    keep = 3
    update = 4
    reject = 5