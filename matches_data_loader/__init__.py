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
    return _data_loader.data()
