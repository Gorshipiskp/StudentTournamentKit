"""Team and player commands."""

from __future__ import annotations

from uuid import uuid4

from app.application.unit_of_work import UnitOfWork
from app.domain.tournament.team_entities import (
    MAX_NAME_LEN,
    MAX_NICKNAME_LEN,
    MAX_PLAYERS_PER_TEAM,
    MAX_STEAM_ID_LEN,
    MAX_TAG_LEN,
    MAX_TEAMS_PER_TOURNAMENT,
    Player,
    Team,
)


class TeamError(Exception):
    def __init__(self, message: str, *, code: str = "invalid") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _require_tournament(uow: UnitOfWork, tournament_id: str) -> None:
    if uow.tournaments.get(tournament_id) is None:
        raise KeyError(f"tournament not found: {tournament_id}")


def _require_team_in_tournament(uow: UnitOfWork, tournament_id: str, team_id: str) -> Team:
    team = uow.teams.get(team_id)
    if team is None or team.tournament_id != tournament_id:
        raise KeyError(f"team not found: {team_id}")
    return team


def create_team(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    name: str,
    tag: str = "",
) -> Team:
    _require_tournament(uow, tournament_id)
    clean_name = (name or "").strip()
    if not clean_name:
        raise TeamError("name required", code="name_required")
    if len(clean_name) > MAX_NAME_LEN:
        raise TeamError(f"name max {MAX_NAME_LEN} chars", code="name_too_long")
    clean_tag = (tag or "").strip()
    if len(clean_tag) > MAX_TAG_LEN:
        raise TeamError(f"tag max {MAX_TAG_LEN} chars", code="tag_too_long")
    if uow.teams.count_for_tournament(tournament_id) >= MAX_TEAMS_PER_TOURNAMENT:
        raise TeamError(
            f"max {MAX_TEAMS_PER_TOURNAMENT} teams per tournament",
            code="team_limit",
        )
    if uow.teams.find_by_name(tournament_id, clean_name) is not None:
        raise TeamError("team name already used in this tournament", code="name_taken")

    team = Team(
        id=str(uuid4()),
        tournament_id=tournament_id,
        name=clean_name,
        tag=clean_tag,
    )
    uow.teams.add(team)
    uow.commit()
    return team


def update_team(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    team_id: str,
    name: str | None = None,
    tag: str | None = None,
) -> Team:
    team = _require_team_in_tournament(uow, tournament_id, team_id)
    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise TeamError("name required", code="name_required")
        if len(clean_name) > MAX_NAME_LEN:
            raise TeamError(f"name max {MAX_NAME_LEN} chars", code="name_too_long")
        existing = uow.teams.find_by_name(tournament_id, clean_name)
        if existing is not None and existing.id != team.id:
            raise TeamError("team name already used in this tournament", code="name_taken")
        team.name = clean_name
    if tag is not None:
        clean_tag = tag.strip()
        if len(clean_tag) > MAX_TAG_LEN:
            raise TeamError(f"tag max {MAX_TAG_LEN} chars", code="tag_too_long")
        team.tag = clean_tag
    uow.teams.save(team)
    uow.commit()
    return team


def delete_team(uow: UnitOfWork, *, tournament_id: str, team_id: str) -> None:
    _require_team_in_tournament(uow, tournament_id, team_id)
    uow.players.delete_for_team(team_id)
    uow.teams.delete(team_id)
    uow.commit()


def create_player(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    team_id: str,
    nickname: str,
    steam_id: str | None = None,
    is_coach: bool = False,
) -> Player:
    _require_team_in_tournament(uow, tournament_id, team_id)
    clean_nick = (nickname or "").strip()
    if not clean_nick:
        raise TeamError("nickname required", code="nickname_required")
    if len(clean_nick) > MAX_NICKNAME_LEN:
        raise TeamError(f"nickname max {MAX_NICKNAME_LEN} chars", code="nickname_too_long")
    clean_steam = (steam_id or "").strip() or None
    if clean_steam and len(clean_steam) > MAX_STEAM_ID_LEN:
        raise TeamError(f"steam_id max {MAX_STEAM_ID_LEN} chars", code="steam_too_long")
    if uow.players.count_for_team(team_id) >= MAX_PLAYERS_PER_TEAM:
        raise TeamError(
            f"max {MAX_PLAYERS_PER_TEAM} players per team",
            code="player_limit",
        )

    player = Player(
        id=str(uuid4()),
        team_id=team_id,
        nickname=clean_nick,
        steam_id=clean_steam,
        is_coach=bool(is_coach),
    )
    uow.players.add(player)
    uow.commit()
    return player


def update_player(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    team_id: str,
    player_id: str,
    nickname: str | None = None,
    steam_id: str | None = None,
    is_coach: bool | None = None,
) -> Player:
    _require_team_in_tournament(uow, tournament_id, team_id)
    player = uow.players.get(player_id)
    if player is None or player.team_id != team_id:
        raise KeyError(f"player not found: {player_id}")
    if nickname is not None:
        clean_nick = nickname.strip()
        if not clean_nick:
            raise TeamError("nickname required", code="nickname_required")
        if len(clean_nick) > MAX_NICKNAME_LEN:
            raise TeamError(f"nickname max {MAX_NICKNAME_LEN} chars", code="nickname_too_long")
        player.nickname = clean_nick
    if steam_id is not None:
        clean_steam = steam_id.strip() or None
        if clean_steam and len(clean_steam) > MAX_STEAM_ID_LEN:
            raise TeamError(f"steam_id max {MAX_STEAM_ID_LEN} chars", code="steam_too_long")
        player.steam_id = clean_steam
    if is_coach is not None:
        player.is_coach = bool(is_coach)
    uow.players.save(player)
    uow.commit()
    return player


def delete_player(
    uow: UnitOfWork,
    *,
    tournament_id: str,
    team_id: str,
    player_id: str,
) -> None:
    _require_team_in_tournament(uow, tournament_id, team_id)
    player = uow.players.get(player_id)
    if player is None or player.team_id != team_id:
        raise KeyError(f"player not found: {player_id}")
    uow.players.delete(player_id)
    uow.commit()
