# Usage Examples
Query the server "example.com" on port 25565:
1) python mcquery.py example.com
2) python mcquery.py example.com 25565

Query the server "example.com" on port 25575:
1) python mcquery.py example.com 25575

Query the default host and port specified by the config:
1) python mcquery.py
1) (Nothing passed - Instead, change defaults below)

# Configurables
Default host and port values if no command line args are passed to the script.
If you always check a single server/port, it's better to change these to that, because
you won't need to constantly pass the same command line args repeatedly.
```py
HOST = "localhost" 
PORT = 25565 
```

Should the script print out everything from both types of queries?
```py
BASIC_STAT = True
FULL_STAT = True
```

Custom user order for both Basic and Full query types
```py
BASICSTAT_PRINT_ORDER = [
    'hostip',
    'hostport',
    'gametype',
    'motd',
    'map',
    'numplayers',
    'maxplayers'
]
```

```py
FULLSTAT_PRINT_ORDER = [
    'hostip',
    'hostport',
    'game_id',
    'gametype',
    'version',
    'server_mod',
    'plugins',
    'motd',
    'map',
    'numplayers',
    'maxplayers',
    'players'
]
```

# Credits
Original script by barneygale:

https://github.com/barneygale/MCQuery

Brought to python3 by hatkidchan:

https://github.com/hatkidchan/MCQuery

Custom version with command line args and other simple configurables by Koi:

https://github.com/Koi-MC/MCQuery
