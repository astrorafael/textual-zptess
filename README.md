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
- Config
```SQL
	SELECT section,property as prop,value
	FROM config_t
	ORDER BY section,prop;
```
- Photometers

```SQL
	SELECT DISTINCT name,mac,sensor,model,firmware,filter,plug,box,collector
	FROM summary_t
	ORDER BY name;
```

- Summary

```SQL
	SELECT DISTINCT name,mac,session,role,calibration,calversion,author,nrounds,offset as zp_offset,
	upd_flag,prev_zp,zero_point,zero_point_method,freq,freq_method,mag,comment
	FROM summary_t
	ORDER BY name;
```

- Rounds
```SQL
	SELECT DISTINCT r.session, r.round, r.role, r.begin_tstamp, r.end_tstamp,r.central, r.freq, r.stddev, r.mag, r.zp_fict, r.zero_point, r.nsamples, r.duration
	FROM rounds_t AS r
	ORDER BY r.session, r.round, r.role;
```
- Samples

```SQL
	SELECT session,tstamp,role,seq,freq,temp_box from samples_t ORDER BY session, tstamp, role;
```

- Batch
```SQL
SELECT * FROM batch_t;
```