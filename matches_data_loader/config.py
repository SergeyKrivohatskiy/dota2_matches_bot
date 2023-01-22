import os


APP_NAME = os.environ['LIQUIPEDIA_APP_NAME']
DATA_UPDATE_TIMEOUT = 300  # seconds. Actual updates may be slower due to API rate limits (liquipedia mostly)
STREAM_SEARCH_BEFORE_MATCH_MINUTES = 15  # minutes. Start searching for match streams before match starts

MAXIMUM_MATCHES_TO_LOAD = 5

TWITCH_STREAMS_UPDATE_TIMEOUT = 100  # seconds
TWITCH_THUMBNAIL_EXPIRE = 3600  # seconds. After this time THUMBNAIL will be removed (not to store too many of them)
TWITCH_CLIENT_ID = os.environ['TWITCH_ID']
TWITCH_CLIENT_SECRET = os.environ['TWITCH_SECRET']
TWITCH_THUMBNAIL_WH = (16 * 24, 9 * 24)  # usually it is 16:9 aspect ratio
