"""Predefined genres used by the movie catalog."""

from enum import StrEnum


class Genre(StrEnum):
    """Supported movie genres."""

    ACTION = "action"
    ADVENTURE = "adventure"
    ANIMATION = "animation"
    COMEDY = "comedy"
    DOCUMENTARY = "documentary"
    DRAMA = "drama"
    FANTASY = "fantasy"
    HORROR = "horror"
    ROMANCE = "romance"
    THRILLER = "thriller"
