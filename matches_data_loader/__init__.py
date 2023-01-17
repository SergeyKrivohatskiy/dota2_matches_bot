import typing
import matches_data_loader.data_loader
from matches_data_loader.data_loader import Dota2Match, TournamentInfo, Dota2Team


_data_loader: typing.Optional[data_loader.DataLoader] = None


def initialize():
    global _data_loader
    assert(_data_loader is None)
    _data_loader = data_loader.DataLoader()


def get_matches() -> typing.List[data_loader.Dota2Match]:
    global _data_loader
    assert(_data_loader is not None)
    return _data_loader.data().upcoming_matches


def get_teams() -> typing.Dict[str, str]:
    global _data_loader
    assert(_data_loader is not None)
    return _data_loader.data().team_names_to_id


def get_tournaments() -> typing.Dict[str, str]:
    global _data_loader
    assert(_data_loader is not None)
    return _data_loader.data().tournament_names_to_id
