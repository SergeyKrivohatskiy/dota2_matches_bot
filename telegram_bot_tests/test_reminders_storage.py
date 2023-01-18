import telegram_bot.reminders_storage as reminders_storage
import pytest

reminders_storage.initialize()

_USER_1 = 'test/user/1/id'
_USER_2 = 'test/user/2/id'
_USER_3 = 'test/user/3/id'

_MATCH_1 = reminders_storage.MatchDescriptor(None, None, 'test_tournament1')
_MATCH_2 = reminders_storage.MatchDescriptor('test_team1', None, 'test_tournament2')
_MATCH_3 = reminders_storage.MatchDescriptor('test_team1', 'test_team2', 'test_tournament2')
_MATCH_4 = reminders_storage.MatchDescriptor(None, 'test_team2', 'test_tournament1')


@pytest.mark.skip('TODO rewrite for db storage')
def test_reminders_storage():
    rs = reminders_storage.storage()
    rs.remove_all_reminders(_USER_1)
    rs.remove_all_reminders(_USER_2)
    rs.remove_all_reminders(_USER_3)

    for match in (_MATCH_1, _MATCH_2, _MATCH_3, _MATCH_4):
        assert(len(rs.get_reminded_chat_ids(match)) == 0)

    rs.add_team_reminder(_USER_1, 'test_team1')
    assert(len(rs.get_reminded_chat_ids(_MATCH_1)) == 0)
    assert ((rs.get_reminded_chat_ids(_MATCH_2)) == {_USER_1})
    assert ((rs.get_reminded_chat_ids(_MATCH_3)) == {_USER_1})
    assert(len(rs.get_reminded_chat_ids(_MATCH_4)) == 0)

    rs.add_tournament_reminder(_USER_1, 'test_tournament1')
    assert ((rs.get_reminded_chat_ids(_MATCH_1)) == {_USER_1})
    assert ((rs.get_reminded_chat_ids(_MATCH_2)) == {_USER_1})
    assert ((rs.get_reminded_chat_ids(_MATCH_3)) == {_USER_1})
    assert ((rs.get_reminded_chat_ids(_MATCH_4)) == {_USER_1})

    rs.remove_all_reminders(_USER_1)
    for match in (_MATCH_1, _MATCH_2, _MATCH_3, _MATCH_4):
        assert(len(rs.get_reminded_chat_ids(match)) == 0)

    rs.add_tournament_reminder(_USER_1, 'test_tournament2')
    assert(len(rs.get_reminded_chat_ids(_MATCH_1)) == 0)
    assert (rs.get_reminded_chat_ids(_MATCH_2) == {_USER_1})
    assert (rs.get_reminded_chat_ids(_MATCH_3) == {_USER_1})
    assert(len(rs.get_reminded_chat_ids(_MATCH_4)) == 0)

    rs.add_all_reminder(_USER_2)
    assert ((rs.get_reminded_chat_ids(_MATCH_1)) == {_USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_2)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_3)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_4)) == {_USER_2})

    rem_1 = rs.get_reminders(_USER_1)
    assert(rem_1 == {reminders_storage.ChatReminder('tournament', 'test_tournament2')})
    rem_2 = rs.get_reminders(_USER_2)
    assert(rem_2 == {reminders_storage.ChatReminder('all', None)})

    rs.add_tournament_reminder(_USER_1, '312421421')
    rs.add_all_reminder(_USER_2)
    rs.add_tournament_reminder(_USER_2, '312421421')
    rs.add_tournament_reminder(_USER_2, '312421411232421')
    rs.add_team_reminder(_USER_1, '312421411232421')
    rs.add_team_reminder(_USER_2, '312421')
    rs.add_team_reminder(_USER_2, '312421')
    rs.add_all_reminder(_USER_1)
    assert ((rs.get_reminded_chat_ids(_MATCH_1)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_2)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_3)) == {_USER_1, _USER_2})
    assert ((rs.get_reminded_chat_ids(_MATCH_4)) == {_USER_1, _USER_2})
    rs.remove_all_reminders(_USER_1)
    rs.remove_all_reminders(_USER_2)
    assert ((rs.get_reminded_chat_ids(_MATCH_1)) == set())
    assert ((rs.get_reminded_chat_ids(_MATCH_2)) == set())
    assert ((rs.get_reminded_chat_ids(_MATCH_3)) == set())
    assert ((rs.get_reminded_chat_ids(_MATCH_4)) == set())
