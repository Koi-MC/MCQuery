#!/usr/bin/python3
import mcquery
import time
from pprint import pprint

host = input('Host (localhost): ')
port = input('Port (25565): ')

if host == '':
    host = 'localhost'
if port == '': 
    port = 25565
else: 
    port = int(port)



print("Connecting...")
q = mcquery.MCQuery(host, port)
print("Connected.")

while True:
    pprint(q.full_stat())
    time.sleep(5)
