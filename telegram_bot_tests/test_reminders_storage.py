import telegram_bot.reminders_storage as reminders_storage


_USER_1 = '/user/1/id'
_USER_2 = '/user/2/id'
_USER_3 = '/user/3/id'

_MATCH_1 = reminders_storage.MatchDescriptor(None, None, 'tournament1')
_MATCH_2 = reminders_storage.MatchDescriptor('team1', None, 'tournament2')
_MATCH_3 = reminders_storage.MatchDescriptor('team1', 'team2', 'tournament2')
_MATCH_4 = reminders_storage.MatchDescriptor(None, 'team2', 'tournament1')


def test_reminders_storage():
    rs = reminders_storage.storage()
    for match in (_MATCH_1, _MATCH_2, _MATCH_3, _MATCH_4):
        assert(len(rs.get_reminded_user_ids(match)) == 0)

    rs.add_team_reminder(_USER_1, 'team1')
    assert(len(rs.get_reminded_user_ids(_MATCH_1)) == 0)
    assert ((rs.get_reminded_user_ids(_MATCH_2)) == {_USER_1})
    assert ((rs.get_reminded_user_ids(_MATCH_3)) == {_USER_1})
    assert(len(rs.get_reminded_user_ids(_MATCH_4)) == 0)

    rs.add_tournament_reminder(_USER_1, 'tournament1')
    assert ((rs.get_reminded_user_ids(_MATCH_1)) == {_USER_1})
    assert ((rs.get_reminded_user_ids(_MATCH_2)) == {_USER_1})
    assert ((rs.get_reminded_user_ids(_MATCH_3)) == {_USER_1})
    assert ((rs.get_reminded_user_ids(_MATCH_4)) == {_USER_1})

    rs.remove_all_reminders(_USER_1)
    for match in (_MATCH_1, _MATCH_2, _MATCH_3, _MATCH_4):
        assert(len(rs.get_reminded_user_ids(match)) == 0)

    rs.add_tournament_reminder(_USER_1, 'tournament2')
    assert(len(rs.get_reminded_user_ids(_MATCH_1)) == 0)
    assert (rs.get_reminded_user_ids(_MATCH_2) == {_USER_1})
    assert (rs.get_reminded_user_ids(_MATCH_3) == {_USER_1})
    assert(len(rs.get_reminded_user_ids(_MATCH_4)) == 0)

    rs.add_all_reminder(_USER_2)
    assert ((rs.get_reminded_user_ids(_MATCH_1)) == {_USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_2)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_3)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_4)) == {_USER_2})

    rem_1 = rs.get_reminders(_USER_1)
    assert(rem_1 == {reminders_storage.UserReminder('tournament', 'tournament2')})
    rem_2 = rs.get_reminders(_USER_2)
    assert(rem_2 == {reminders_storage.UserReminder('all', None)})

    rs.add_tournament_reminder(_USER_1, '312421421')
    rs.add_all_reminder(_USER_2)
    rs.add_tournament_reminder(_USER_2, '312421421')
    rs.add_tournament_reminder(_USER_2, '312421411232421')
    rs.add_team_reminder(_USER_1, '312421411232421')
    rs.add_team_reminder(_USER_2, '312421')
    rs.add_team_reminder(_USER_2, '312421')
    rs.add_all_reminder(_USER_1)
    assert ((rs.get_reminded_user_ids(_MATCH_1)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_2)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_3)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_user_ids(_MATCH_4)) == {_USER_1, _USER_2})
    rs.remove_all_reminders(_USER_1)
    rs.remove_all_reminders(_USER_2)
    assert ((rs.get_reminded_user_ids(_MATCH_1)) == set())
    assert ((rs.get_reminded_user_ids(_MATCH_2)) == set())
    assert ((rs.get_reminded_user_ids(_MATCH_3)) == set())
    assert ((rs.get_reminded_user_ids(_MATCH_4)) == set())
