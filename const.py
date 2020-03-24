APPNAME = 'antibox'
__VERSION__ = '0.1.0'
INDENT = '  '
VERBOSITY_MODES = {
    0: 'ERROR',
    1: 'INFO',
    2: 'DEBUG'
}
HELPMSG = f'''{APPNAME} v{__VERSION__}
usage: {APPNAME} (-h <HOSTNAME> | -m <MAC_ADDRESS>) -r <RULE_NAME> [-v <({'|'.join(VERBOSITY_MODES.values())})>] [--help]

    Get current IP of device
    {INDENT * 1}-h, --hostname      {INDENT * 2}By hostname
    {INDENT * 1}-m, --mac           {INDENT * 2}By MAC address

    {INDENT * 1}-r, --rule          {INDENT * 2}Name of the rule to modify

    {INDENT * 1}-v, --verbosity     {INDENT * 2}Set the verbosity.
                                Available options: [{', '.join(VERBOSITY_MODES.values())}]
    {INDENT * 1}--help              {INDENT * 2}Print this message
'''