
APP_NAME = 'https://t.me/dota_upcoming_matches_bot (sergey@krivohatskiy.com)'
DATA_UPDATE_TIMEOUT = 300  # seconds. Actual updates may be slower due to API rate limits (liquipedia mostly)
STREAM_SEARCH_BEFORE_MATCH_MINUTES = 15  # minutes. Start searching for match streams before match starts

MAXIMUM_MATCHES_TO_LOAD = 5

TWITCH_STREAMS_UPDATE_TIMEOUT = 100  # seconds
TWITCH_THUMBNAIL_EXPIRE = 3600  # seconds. After this time THUMBNAIL will be removed (not to store too many of them)
TWITCH_CLIENT_ID = '43q9et1ah6j7qklol5i3shhbpd1bdo'
TWITCH_CLIENT_SECRET = '3kiqk9bza163tzus8vpjzij83v5fe0'
TWITCH_THUMBNAIL_WH = (16 * 24, 9 * 24)  # usually it is 16:9 aspect ratio
