class BaseError(Exception):
    pass


class NoGameFound(BaseError):
    pass


class OpponentLeft(BaseError):
    pass


class GameAlreadyFinished(BaseError):
    pass


class InvalidStep(BaseError):
    pass
