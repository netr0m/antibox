APPNAME = 'antibox'
__VERSION__ = '0.2.1'
INDENT = '  '
VERBOSITY_MODES = {
    0: 'ERROR',
    1: 'INFO',
    2: 'DEBUG'
}
HELPMSG = f'''{APPNAME} v{__VERSION__}
usage: {APPNAME} (-h <HOSTNAME> | -m <MAC_ADDRESS>) -r <RULE_NAME> [-a <LIST>] [-v <({'|'.join(VERBOSITY_MODES.values())})>] [-l <PATH>] [--help]

    Get current IP of device:
    {INDENT * 1}-h, --hostname      {INDENT * 2}By hostname
    {INDENT * 1}-m, --mac           {INDENT * 2}By MAC address

    {INDENT * 1}-r, --rule          {INDENT * 2}Name of the rule to modify

    Multiple entries
    {INDENT * 1}-a, --all           {INDENT * 2}A comma-separated list of devices and rules in the following format:
                                `[hostname]|[mac]|rule`. E.g. `debian||vpn_rule,|raspberry|plex_rule`.

    {INDENT * 1}-v, --verbosity     {INDENT * 2}Set the verbosity.
                                Available options: [{', '.join(VERBOSITY_MODES.values())}]
    {INDENT * 1}-l, --logpath       {INDENT * 2}Path to the directory for log files

    {INDENT * 1}--help              {INDENT * 2}Print this message
'''