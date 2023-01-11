from liquipedia_dota_api import Dota2Api


_APP_NAME = 'liquipedia Dota2Api tests (sergey@krivohatskiy.com)'

_DOTA2_API = Dota2Api(app_name=_APP_NAME)


def test_get_matches():
    matches = _DOTA2_API.get_matches()
    assert len(matches) > 0
    match_0 = matches[0]
    assert match_0.format


def test_get_teams():
    teams = _DOTA2_API.get_teams()
    assert len(teams) > 0
    teams_0 = teams[0]
    assert teams_0.name
    assert teams_0.icon
    assert teams_0.region
    assert teams_0.liquipedia_page


def test_get_tournaments():
    tournaments = _DOTA2_API.get_tournaments()
    assert len(tournaments) > 0
    tournament_0 = tournaments[0]
    assert tournament_0.name
    assert tournament_0.liquipedia_page
