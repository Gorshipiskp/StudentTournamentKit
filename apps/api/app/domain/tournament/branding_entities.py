"""Tournament branding (logo / colors / optional bg)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

LOGO_MAX_BYTES = 2 * 1024 * 1024  # 2MB
BG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/webp", "image/gif"}
)


@dataclass
class TournamentBranding:
    tournament_id: str
    colors_json: dict[str, Any] = field(default_factory=dict)
    logo_blob: bytes | None = None
    logo_content_type: str | None = None
    bg_blob: bytes | None = None
    bg_content_type: str | None = None

    def has_logo(self) -> bool:
        return bool(self.logo_blob)

    def has_bg(self) -> bool:
        return bool(self.bg_blob)

    def logo_version(self) -> str | None:
        if not self.logo_blob:
            return None
        return hashlib.sha256(self.logo_blob).hexdigest()[:12]

    def bg_version(self) -> str | None:
        if not self.bg_blob:
            return None
        return hashlib.sha256(self.bg_blob).hexdigest()[:12]

    def to_public_meta(self) -> dict[str, Any]:
        return {
            "tournament_id": self.tournament_id,
            "colors": dict(self.colors_json or {}),
            "has_logo": self.has_logo(),
            "has_bg": self.has_bg(),
            "logo_content_type": self.logo_content_type if self.has_logo() else None,
            "bg_content_type": self.bg_content_type if self.has_bg() else None,
            "logo_version": self.logo_version(),
            "bg_version": self.bg_version(),
        }

    def to_overlay_branding(self) -> dict[str, Any]:
        """Fields merged into overlay snapshot data.branding."""
        tid = self.tournament_id
        out: dict[str, Any] = {
            "colors": dict(self.colors_json or {}),
            "logo_url": None,
            "bg_url": None,
        }
        if self.has_logo():
            ver = self.logo_version()
            out["logo_url"] = f"/api/v1/tournaments/{tid}/branding/logo?v={ver}"
        if self.has_bg():
            ver = self.bg_version()
            out["bg_url"] = f"/api/v1/tournaments/{tid}/branding/bg?v={ver}"
        return out
