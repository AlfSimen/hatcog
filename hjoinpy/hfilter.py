
import sys
import json

PATTERNS_OUT = {

        # Custom command for us to send the password
        '/pw': u'PRIVMSG NickServ :identify %(msg)s',

        # User ACTION
        '/me': u'PRIVMSG %(channel)s :\u0001ACTION %(msg)s\u0001',

        # Any command
        '__default_cmd__': u'%(cmd)s %(msg)s',

        # A regular message
        '__default_msg__': u'PRIVMSG %(channel)s :%(msg)s',
}

PATTERNS_IN = {
    'NOTICE': u'%(content)s',
    'NICK': u'* %(user)s is now known as %(content)s',
    'JOIN': u'* %(user)s joined the channel',
    'PART': u'* %(user)s left the channel',
    'PRIVMSG': u'[%(user)s] \t %(content)s',
    'QUIT': u'%(user)s has quit',
    'MODE': u'Mode set to %(content)s',

    # Message of the day
    '372': u'%(content)s',

    # Topic
    '332': u'Topic: %(content)s',

    # NAMES reply
    '353': u'Users currently in %(channel)s: %(content)s',

    # IRC ops online
    '252': u'%(content)s %(arg1)s',

    # Who set the topic
    '333': u'Topic set by %(arg2)s',

    # This channel's URL
    '328': u'Channel url: %(content)s',

    '__default__': u'%(content)s'
}

IGNORE = [
    '005',  # Extensions server supports
    '253',  # Num unknown connections
    '254',  # Num channels
    '255',  # Num clients and servers
    '366',  # End of NAMES
    '376',  # End of MOTD
]

DEFAULT = [
    '001',
    '002',
    '003',
    '004',
    '265',
    '266',
    '250',
    '251',
    '375'
]

def lowercase_keys(dict_obj):
    """Convert map keys to lower case"""
    for key in dict_obj.keys():
        if not key.lower() in dict_obj:
            dict_obj[key.lower()] = dict_obj[key]
            del dict_obj[key]


def add_args(dict_obj):
    """Convert array of args to numbered,
    so that our patterns can access them.
    """

    index = 0
    for item in dict_obj['args']:
        dict_obj['arg%d' % index] = item
        index += 1

def translate_in(line):
    """Translate a JSON line from the server
    into display string.
    """
    line = line.strip()
    if not line:
        return None

    obj = json.loads(line)
    lowercase_keys(obj)
    cmd = obj['command']
    if cmd in IGNORE:
        return None

    add_args(obj)

    pattern = PATTERNS_IN['__default__']
    if cmd in PATTERNS_IN:
        pattern = PATTERNS_IN[cmd]

    # Timestamp everything if requested to
    if '--timestamp' in sys.argv:
        pattern = '%(received)s ' + pattern

    output = pattern % obj
    return output.encode('utf8')


def translate_out(channel, line):
    """Translate a user input into IRC message."""
    line = line.strip()
    if not line:
        return None

    params = {'channel': channel}

    if is_irc_command(line):
        parts = line[1:].split(' ')
        cmd = parts[0]
        params['cmd'] = cmd

        msg = ' '.join(parts[1:])

        pattern = PATTERNS_OUT['__default_cmd__']
        if cmd in PATTERNS_OUT:
            pattern = PATTERNS_OUT[cmd]

    else:
        # Regular IRC message
        msg = line
        pattern = PATTERNS_OUT['__default_msg__']

    params['msg'] = msg

    output = pattern % params
    return output.encode('utf8')


def is_irc_command(line):
    """Is the given line an IRC command line, as opposed to a message"""
    return line.startswith('/')


# When run as a script, translate everything we see on stdin
if __name__ == '__main__':

    result = None
    if '--in' in sys.argv:
        func_translate = translate_in
    elif '--out' in sys.argv:
        func_translate = lambda x : translate_out(sys.argv[2], x)
    else:
        print('Usage: some_data | hfilter.py [--in|--out] [channel]')
        sys.exit(1)

    for line in sys.stdin:

        result = func_translate(line)

        if result:
            print(result)
