import socket
import struct
import argparse
from pprint import pprint

# Credits
#
# Original script by barneygale:
# https://github.com/barneygale/MCQuery
#
# Brought to python3 by hatkidchan:
# https://github.com/hatkidchan/MCQuery
#
# Custom version with command line args and other simple configurables by Koi:
# https://github.com/Koi-MC/MCQuery

# Usage Examples
#
# Query the server "example.com" on port 25565:
# 1) python mcquery.py example.com
# 2) python mcquery.py example.com 25565
#
# Query the server "example.com" on port 25575:
# 1) python mcquery.py example.com 25575
#
# Query the default host and port specified by the config:
# 1) python mcquery.py
# 1) (Nothing passed - Instead, change defaults below)

###########################################
############## CONFIGURABLES ##############
###########################################

#Default host and port values if no command line args are passed to the script.
#If you always check a single server/port, it's better to change these to that, because
#you won't need to constantly pass the same command line args repeatedly.
HOST = "localhost" 
PORT = 25565 

#Should the script print out everything from both types of queries?
BASIC_STAT = True
FULL_STAT = True

#Custom user order for both Basic and Full query types
BASICSTAT_PRINT_ORDER = [
    'hostip',
    'hostport',
    'gametype',
    'motd',
    'map',
    'numplayers',
    'maxplayers'
]

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

###########################################
###########################################
###########################################

class MCQuery:
    id = 0
    retries = 0
    max_retries = 3
    timeout = 10
    decode_format = "iso-8859-1"
    
    def __init__(self, host, port, **kargs):
        self.addr = (host, port)
        if 'max_retries' in kargs:
            self.max_retries = kargs['max_retries']
        if 'timeout' in kargs:
            self.timeout = kargs['timeout']
       
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(self.timeout)
        self.handshake()

    def write_packet(self, type, payload):
        o = b'\xFE\xFD' + struct.pack('>B', type) + struct.pack('>l', self.id) + payload
        try:
            self.socket.sendto(o, self.addr)
        except socket.gaierror as e:
            print(f"An error occurred: The address '"+HOST+"' is unreachable or invalid.\n- Double check spelling.\n- Is the host offline?")
            raise SystemExit
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    
    def read_packet(self):
        buff = self.socket.recvfrom(2048)[0]
        type = buff[0]
        id   = struct.unpack('>l', buff[1:5])[0]
        return type, id, buff[5:]
    
    def handshake(self):
        self.id += 1
        self.write_packet(9, b'')
        try:
            type, id, buff = self.read_packet()
        except:
            self.retries += 1
            print("Failed handshake attempt number",self.retries,"/",self.max_retries,"...")
            if self.retries == self.max_retries:
                raise Exception("Handshake retry limit reached.\n" +
                                "- Is the IP/Port correct?\n- Is the server down?\n- Does the server have queries disabled?")
            return self.handshake()
        
        self.retries = 0
        self.challenge = struct.pack('>l', int(buff[:-1]))
    
    def basic_stat(self):
        self.write_packet(0, self.challenge)
        try:
            type, id, buff = self.read_packet()
        except:
            self.handshake()
            return self.basic_stat()
        
        data = {}
        
        #I don't seem to be receiving this field...
        #data['ip'] = socket.inet_ntoa(buff[:4])[0]
        #buff = buff[4:]
        
        #Grab the first 5 string fields
        data['motd'], \
        data['gametype'], \
        data['map'], \
        data['numplayers'], \
        data['maxplayers'], \
        buff = buff.decode(self.decode_format).split('\x00', 5)
        
        #Unpack a big-endian short for the port
        if isinstance(buff, str):
            buff = buff.encode(self.decode_format)
        data['hostport'] = struct.unpack('<h', buff[:2])[0]
        
        #Grab final string component: host name
        data['hostip'] = buff[2:-1].decode(self.decode_format)
        
        #Encode integer fields
        for k in ('numplayers', 'maxplayers'):
            data[k] = int(data[k])

        #Create remapped dict obj pre-sorted, pre-decoded
        basic_info_dict = {
            'gametype': data['gametype'],
            'hostip': data['hostip'],
            'hostport': data['hostport'],
            'map': data['map'],
            'maxplayers': data['maxplayers'],
            'motd': data['motd'],
            'numplayers': data['numplayers']
        }

        #Do custom sort
        custom_ordered_output = {key: basic_info_dict[key] for key in BASICSTAT_PRINT_ORDER if key in basic_info_dict}

        return custom_ordered_output
    
    def full_stat(self):
        #Pad request to 8 bytes
        self.write_packet(0, self.challenge + b'\x00\x00\x00\x00')
        try:
            type, id, buff = self.read_packet()
        except:
            self.handshake()
            return self.full_stat()    
        
        #Chop off useless stuff at beginning
        buff = buff[11:]
        
        #Split around notch's silly token
        items, players = buff.split(b'\x00\x00\x01player_\x00\x00')
        
        #Notch wrote "hostname" where he meant to write "motd"
        items = b'motd' + items[8:] 
        
        #Encode (k1, v1, k2, v2 ..) into a dict
        items = (items.decode(self.decode_format)).split('\x00')
        data = dict(zip(items[::2], items[1::2])) 

        #Remove final two null bytes
        players = players[:-2]
        
        #Split player list
        if players: 
            data['players'] = (players.decode(self.decode_format)).split('\x00')
        else:
            data['players'] = []
        
        #Encode ints
        for k in ('numplayers', 'maxplayers', 'hostport'):
            data[k] = int(data[k])
        
        #Parse 'plugins'`
        #These things are confusing as heck because nobody allows viewing them so I'm just playing it as safe as possible
        if isinstance(data['plugins'], bytes):
            s = data['plugins'].decode(self.decode_format)  # Decode if it's bytes ¯\_(ツ)_/¯
        else:
            s = data['plugins']  # Use it directly if it's already a string ¯\_(ツ)_/¯
        s = s.split(': ', 1)
        data['server_mod'] = s[0]
        if len(s) == 1:
            data['plugins'] = []
        elif len(s) == 2:
            data['plugins'] = s[1].split('; ')

        #Create remapped dict obj pre-sorted, pre-decoded
        full_info_dict = {
            'game_id': data['game_id'],
            'gametype': data['gametype'],
            'hostip': data['hostip'],
            'hostport': data['hostport'],
            'map': data['map'],
            'maxplayers': data['maxplayers'],
            'motd': data['motd'],
            'numplayers': data['numplayers'],
            'players': data['players'],
            'plugins': data['plugins'],
            'server_mod': data['server_mod'],
            'version': data['version']
        }

        #Do custom sort
        custom_ordered_output = {key: full_info_dict[key] for key in FULLSTAT_PRINT_ORDER if key in full_info_dict}

        return custom_ordered_output


def pass_args():
    parser = argparse.ArgumentParser(description='Minecraft Server Query Tool')
    parser.add_argument('host', type=str, nargs='?', default=HOST, help='The host (IP or domain) of the Minecraft server')
    parser.add_argument('port', type=int, nargs='?', default=PORT, help='The port of the Minecraft server')
    args = parser.parse_args()
    if args.host == HOST and args.port == PORT:
        print("No command line arguments were provided. Using user specified default values:")
        print(f"Specified Default Host: {args.host}, Specified Default Port: {args.port}")
    return args.host, args.port


if __name__ == "__main__":
    #Get command line args
    HOST, PORT = pass_args()

    #Perform the query attempt
    try:
        print("Querying host '"+HOST+"' on port",PORT)
        q = MCQuery(HOST, PORT)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise SystemExit

    #If query is available and responsive, print out the desired responses
    if BASIC_STAT:
        print("Basic Stat Response:")
        pprint(q.basic_stat(), sort_dicts=False)
        print("\n")
    if FULL_STAT:
        print("Full Stat Response:")
        pprint(q.full_stat(), sort_dicts=False)
        print("\n")
