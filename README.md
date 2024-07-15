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

# Notes

from [Tasck Overflow](https://stackoverflow.com/questions/71631247/textual-python-tui-enabling-long-running-external-asyncio-functionality)
Textual widgets have an internal message queue that processes events sequentially. Your on_mount handler is processing one of these events, but because it is an infinite loop, you are preventing further events for being processed.

If you want to process something in the background you will need to creat a new asyncio Task. Note that you can’t await that task, since that will also prevent the handler from returning.

## Migration SQL

-- oold
SELECT name,mac,freq,freq_method,mag, abs(mag- (20.50-2.5*log10(freq))), abs(mag- (20.44-2.5*log10(freq))),
abs(mag- (20.50-2.5*log10(freq))) < 0.005 as flag250, abs(mag- (20.44-2.5*log10(freq))) < 0.005 as flag244, session,role,offset AS zp_offset
FROM summary_t
where flag250 = 0 and flag244 = 1
ORDER BY name

-- new
SELECT phot_id,freq,freq_method,mag, abs(mag- (20.50-2.5*log10(freq))), abs(mag- (20.44-2.5*log10(freq))),
abs(mag- (20.50-2.5*log10(freq))) < 0.005 as flag250, abs(mag- (20.44-2.5*log10(freq))) < 0.005 as flag244, session,role, zp_offset
FROM summary_t
where flag250 = 0 and flag244 = 1
ORDER BY phot_id




update summary_t
set mag = 20.50-2.5*log10(freq)
where mag in (
	SELECT mag from summary_t
	where abs(mag- (20.44-2.5*log10(freq))) < 0.005
) and freq is not null
