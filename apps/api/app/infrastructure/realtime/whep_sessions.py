"""In-memory WHEP play leases — max 2 concurrent holders per match (F9)."""



from __future__ import annotations



import threading

import time

from dataclasses import dataclass





@dataclass

class WhepLease:

    jti: str

    expires_at: float

    invite_id: str





class WhepSessionRegistry:

    """Process-local cap for protocol 2 WHEP credentials (single API replica).



    Limit is **2 distinct invite holders** per match. Re-issue for the same

    invite (page refresh / reconnect) replaces that invite's lease.

    """



    def __init__(self, *, max_per_match: int = 2) -> None:

        self._max = max_per_match

        self._lock = threading.Lock()

        self._leases: dict[str, list[WhepLease]] = {}



    def reset(self) -> None:

        with self._lock:

            self._leases.clear()



    def active_count(self, match_id: str, *, now: float | None = None) -> int:

        with self._lock:

            self._prune(match_id, now=now)

            return len(self._leases.get(match_id, []))



    def try_acquire(

        self,

        match_id: str,

        *,

        jti: str,

        expires_at: float,

        invite_id: str,

        now: float | None = None,

    ) -> bool:

        holder = (invite_id or "").strip()

        if not holder:

            return False

        with self._lock:

            self._prune(match_id, now=now)

            room = self._leases.setdefault(match_id, [])

            for i, lease in enumerate(room):

                if lease.invite_id == holder:

                    room[i] = WhepLease(jti=jti, expires_at=expires_at, invite_id=holder)

                    return True

            if len(room) >= self._max:

                return False

            room.append(WhepLease(jti=jti, expires_at=expires_at, invite_id=holder))

            return True



    def release(self, match_id: str, jti: str) -> None:

        with self._lock:

            room = self._leases.get(match_id) or []

            self._leases[match_id] = [x for x in room if x.jti != jti]



    def release_invite(self, match_id: str, invite_id: str) -> None:

        holder = (invite_id or "").strip()

        with self._lock:

            room = self._leases.get(match_id) or []

            kept = [x for x in room if x.invite_id != holder]

            if kept:

                self._leases[match_id] = kept

            elif match_id in self._leases:

                del self._leases[match_id]



    def _prune(self, match_id: str, *, now: float | None = None) -> None:

        clock = now if now is not None else time.time()

        room = self._leases.get(match_id) or []

        kept = [x for x in room if x.expires_at > clock]

        if kept:

            self._leases[match_id] = kept

        elif match_id in self._leases:

            del self._leases[match_id]





whep_sessions = WhepSessionRegistry(max_per_match=2)


