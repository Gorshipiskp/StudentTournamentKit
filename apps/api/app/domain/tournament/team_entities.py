"""Team and player domain entities."""

from __future__ import annotations

from dataclasses import dataclass

MAX_TEAMS_PER_TOURNAMENT = 32
MAX_PLAYERS_PER_TEAM = 6  # 5 + coach
MAX_NAME_LEN = 64
MAX_TAG_LEN = 16
MAX_NICKNAME_LEN = 64
MAX_STEAM_ID_LEN = 32


@dataclass
class Team:
    id: str
    tournament_id: str
    name: str
    tag: str = ""

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "name": self.name,
            "tag": self.tag,
        }


@dataclass
class Player:
    id: str
    team_id: str
    nickname: str
    steam_id: str | None = None
    is_coach: bool = False

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "team_id": self.team_id,
            "nickname": self.nickname,
            "steam_id": self.steam_id,
            "is_coach": self.is_coach,
        }
