"""Game integration domain — normalized events/commands (adapter boundary)."""

from app.domain.game_integration.schemas import (
    PROTOCOL_VERSION,
    CommandAckDict,
    CommandRequestDict,
    CommandType,
    EventType,
    GameEventDict,
    GameSnapshotDict,
)

__all__ = [
    "PROTOCOL_VERSION",
    "CommandAckDict",
    "CommandRequestDict",
    "CommandType",
    "EventType",
    "GameEventDict",
    "GameSnapshotDict",
]
