import json
from abc import ABC
from dataclasses import dataclass, asdict
from typing import Union


@dataclass(frozen=True)
class Message(ABC):
    def asdict(self) -> dict:
        return asdict(self)

    def dump(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def load(cls, buf: Union[bytes, str]) -> "Message":
        if isinstance(buf, str):
            buf = buf.encode()
        return cls(**json.loads(buf))


@dataclass(frozen=True)
class FindGameRequest(Message):
    player: str
    is_remove: bool = False
    room: str = None


@dataclass(frozen=True)
class FindGameResponse(Message):
    """
    >>> msg = FindGameResponse.load(b'{"opponent": "x", "first": false}')
    >>> msg.dump()
    b'{"opponent": "x", "first": false}'
    """

    opponent: str
    first: bool


@dataclass(frozen=True)
class GameFound(Message):
    found: bool
    first: bool


@dataclass(frozen=True)
class GameStep(Message):
    opponent: bool = False
    cell: int = -1
    status: int = 0
    valid: bool = True
    opponent_left: bool = False
    undo: bool = False


@dataclass(frozen=True)
class StepRequest(Message):
    cell: int = -1
    undo: bool = False
