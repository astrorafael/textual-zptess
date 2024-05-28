# textual-zptess
An experimental ZPTESS utility written in Textual

# enviromental file
.env file shoudl contain:

```bash
DATABASE_URL="sqlite+pysqlite:///zptess.db"
DATABASE_URL_ASYNC="sqlite+aiosqlite:///zptess.db"
REF_ENDPOINT=serial:/dev/ttyUSB0:9600
TEST_ENDPOINT=udp:0.0.0.0:2255
```