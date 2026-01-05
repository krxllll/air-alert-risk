from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OblastStatus = Literal["active", "partial", "none", "unknown"]


@dataclass(frozen=True)
class Oblast:
    uid: int
    name: str


OBLASTS_ORDERED: list[Oblast] = [
    Oblast(29, "Автономна Республіка Крим"),
    Oblast(8, "Волинська область"),
    Oblast(4, "Вінницька область"),
    Oblast(9, "Дніпропетровська область"),
    Oblast(28, "Донецька область"),
    Oblast(10, "Житомирська область"),
    Oblast(11, "Закарпатська область"),
    Oblast(12, "Запорізька область"),
    Oblast(13, "Івано-Франківська область"),
    Oblast(31, "м. Київ"),
    Oblast(14, "Київська область"),
    Oblast(15, "Кіровоградська область"),
    Oblast(16, "Луганська область"),
    Oblast(27, "Львівська область"),
    Oblast(17, "Миколаївська область"),
    Oblast(18, "Одеська область"),
    Oblast(19, "Полтавська область"),
    Oblast(5, "Рівненська область"),
    Oblast(30, "м. Севастополь"),
    Oblast(20, "Сумська область"),
    Oblast(21, "Тернопільська область"),
    Oblast(22, "Харківська область"),
    Oblast(23, "Херсонська область"),
    Oblast(3, "Хмельницька область"),
    Oblast(24, "Черкаська область"),
    Oblast(26, "Чернівецька область"),
    Oblast(25, "Чернігівська область"),
]


def decode_by_oblast_char(ch: str) -> OblastStatus:
    """
    alerts.in.ua by_oblast format:
    - 'A' => active
    - 'P' => partial
    - 'N' => none
    """
    if ch == "A":
        return "active"
    if ch == "P":
        return "partial"
    if ch == "N":
        return "none"
    return "unknown"
