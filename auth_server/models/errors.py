class BaseModelException(Exception):
    pass


class DoesNotExist(BaseModelException):
    pass


class ConstraintViolation(BaseModelException):
    pass


class DuplicateConstraint(ConstraintViolation):
    pass
