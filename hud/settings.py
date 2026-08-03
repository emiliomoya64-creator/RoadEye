from __future__ import annotations

from core.config_manager import config


class HUDSettings:
    """
    Acceso centralizado a la configuración visual del HUD.

    Los valores se consultan en cada frame para que, más adelante,
    los cambios realizados desde la rueda dentada puedan reflejarse
    sin reiniciar RoadEye.
    """

    DEFAULT_SHOW = {
        "recording": True,
        "parking": True,
        "gps": True,
        "speed": True,
        "snapshot": True,
        "gallery": True,
        "speed_limit": True,
        "road": True,
        "coordinates": True,
        "date": True,
        "time": True,
        "settings": True,
    }

    @property
    def enabled(self) -> bool:
        return bool(
            config.get(
                "hud.enabled",
                True,
            )
        )

    @property
    def profile(self) -> str:
        value = str(
            config.get(
                "hud.profile",
                "normal",
            )
        ).strip().lower()

        if value not in {
            "minimal",
            "normal",
            "professional",
        }:
            return "normal"

        return value

    @property
    def info_position(self) -> str:
        value = str(
            config.get(
                "hud.info_position",
                "bottom",
            )
        ).strip().lower()

        if value not in {
            "top",
            "bottom",
        }:
            return "bottom"

        return value

    @property
    def top_opacity(self) -> float:
        return self._opacity(
            config.get(
                "hud.top_opacity",
                0.66,
            ),
            0.66,
        )

    @property
    def info_opacity(self) -> float:
        return self._opacity(
            config.get(
                "hud.info_opacity",
                0.58,
            ),
            0.58,
        )

    def visible(
        self,
        widget_name: str,
    ) -> bool:
        normalized = str(
            widget_name
        ).strip().lower()

        default = self.DEFAULT_SHOW.get(
            normalized,
            True,
        )

        return bool(
            config.get(
                f"hud.show.{normalized}",
                default,
            )
        )

    def snapshot(self) -> dict:
        return {
            "enabled": self.enabled,
            "profile": self.profile,
            "info_position": self.info_position,
            "top_opacity": self.top_opacity,
            "info_opacity": self.info_opacity,
            "show": {
                name: self.visible(name)
                for name in self.DEFAULT_SHOW
            },
        }

    @staticmethod
    def _opacity(
        value,
        default: float,
    ) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            result = default

        return max(
            0.0,
            min(
                1.0,
                result,
            ),
        )


hud_settings = HUDSettings()
