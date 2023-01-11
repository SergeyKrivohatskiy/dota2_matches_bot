import typing
import datetime
from dataclasses import dataclass


@dataclass(eq=False)
class Dota2Team:
    name: str
    region: str
    liquipedia_page: str
    icon: str


@dataclass(eq=False)
class Dota2Tournament:
    name: str
    liquipedia_page: str
    tier: str
    date: str
    prize_pool_dollars: typing.Optional[int]
    teams_count: int
    location: str


@dataclass(eq=False)
class Dota2TeamInMatch:
    name: str
    liquipedia_page: str
    icon: str


@dataclass(eq=False)
class TournamentInfoInMatch:
    name: str
    liquipedia_page: str
    icon: str


@dataclass(eq=False)
class Dota2Match:
    team1: typing.Optional[Dota2TeamInMatch]  # None means team is to be determined
    team2: typing.Optional[Dota2TeamInMatch]  # None means team is to be determined
    tournament: TournamentInfoInMatch
    score: typing.Optional[typing.Tuple[int, int]]  # only present for games in progress
    format: typing.Optional[str]  # None means unknown
    start_time: typing.Optional[datetime.datetime]  # None means game is in progress
