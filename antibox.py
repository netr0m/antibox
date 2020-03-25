#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import getopt
import json
import os
import random as rnd
import sys

import requests

from const import HELPMSG, VERBOSITY_MODES

USER = os.getenv('ALTIBOX_USER')
PASS = os.getenv('ALTIBOX_PASS')
HOSTNAME = os.getenv('DEVICE_NAME')
MAC_ADDR = os.getenv('DEVICE_MAC')
FW_RULE = os.getenv('RULE_NAME')
ALL = os.getenv('ANTIBOX_ALL')
ENTRIES = []

VERBOSITY = 1
if os.getenv('VERBOSITY'):
    level = [ k for k,v in VERBOSITY_MODES.items() if v == os.getenv('VERBOSITY') ]
    if level:
        VERBOSITY = level[0]

LOGPATH = os.getcwd()
if os.getenv('LOGPATH'):
    path = os.getenv('LOGPATH')
    if os.path.isdir(path):
        LOGPATH = path


BASE_URL = 'https://www.altibox.no/api'
PATHS = {
    'auth': '/authentication/authenticate',
    'devices': '/wifi/getlandevices',
    'fw': '/wifi/updatewififorlocation',
    'config': '/wifi/getwifibylocation'
}

HEADERS = {
    'Host': 'www.altibox.no',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': ''
}
COOKIE = {
    'sessionTicketApi': None,
    'user': None
}


def log(message, level):
    if level <= VERBOSITY:
        level_str = VERBOSITY_MODES.get(level, 'INFO')
        if level_str == 'INFO':
            level_str += ' '
        now = datetime.datetime.now()
        msg = f'{now} | {level_str} | {message}'
        print(msg)
        if LOGPATH:
            with open(LOGPATH + '/antibox.log', 'a') as f:
                f.write(f'{msg}\n')


def prepare_config(config):
    """Adds missing attributes and changes incorrect data types

        Parameters
        ----------
        config : obj
            The Altibox config to process.

        Returns
        -------
        config : str
            A JSON string representing the Altibox config.
    """
    config['wifiBand2IsSet'] = True
    config['wifiBand5IsSet'] = True

    routes = config.get('router').get('routes')
    for key, val in routes.items():
        for k,v in val.items():
            if k != 'id':
                val[k] = str(v)
        routes[key] = val
    config['router']['routes'] = routes

    wifis = config.get('wifis')
    for key, val in wifis.items():
        wifis[key]['currentChannelIsOver48'] = False
        wifis[key]['hasMultipleWifi'] = True
    config = json.dumps(config)

    return config


def authenticate():
    """Authenticates the user against the Altibox API.

        Parameters
        ----------

        Returns
        -------
        session : str
            A string containing the SessionToken for the API.

        user : obj
            An object representing the authenticated user.
    """
    if USER and PASS:
        url = BASE_URL + PATHS.get('auth') + '?method=BY_USERNAME'
        auth = (USER, PASS)

        HEADERS['Referer'] = 'https://www.altibox.no/login/'
        res = requests.get(url, headers=HEADERS, auth=auth)

        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                data = data.get('data')
                session = data.get('sessionTicket').get('identifier')
                user = data.get('user')
                log(f'AUTH => Authentication successful.', 2)
                log(f'  Authenticated as {user.get("firstName")} {user.get("lastName")}.', 2)
                return session, user
            else:
                err = f'AUTH => Altibox: {data.get("message")}.'
                raise RuntimeError(err)
        else:
            log(f'AUTH => Status code is not 200:', 0)
            log(f'  Status    => {res.status_code}', 0)
            log(f'  Response  => {res.text}', 0)
    else:
        err = f'AUTH => No credentials found. Exiting.'
        raise KeyError(err)


def get_device(hostname=None, mac=None):
    """Fetches a device from the API by either hostname or MAC address.

        Parameters
        ----------
        hostname : str
            The hostname of the device to fetch.

        mac : str
            The MAC address of the device to fetch.

        Returns
        -------
        client : obj
            An object representing the device.
    """
    if COOKIE.get('sessionTicketApi'):
        url = BASE_URL + PATHS.get('devices') + '?activeOnly=false&siteid=2373251&_=1585042725601'
        HEADERS['Referer'] = 'https://www.altibox.no/mine-sider/internett/min-hjemmesentral/'
        HEADERS['X-Requested-With'] = 'XMLHttpRequest'
        
        res = requests.get(url, headers=HEADERS, cookies=COOKIE)

        if res.status_code == 200:
            data = res.json()
            if data:
                clients = data.get('networkClients')
                if hostname:
                    key = 'hostname'
                    val = hostname
                elif mac:
                    key = 'macAddress'
                    val = mac
                else:
                    err = f'GET_DEVICE => No `hostname` or `MAC` specified.'
                    raise AttributeError(err)
                client = list(filter(lambda c: c.get(key) == val, clients))
                if client:
                    client = client[0]
                    log(f'GET_DEVICE => Found client (src={key}:{val}).', 2)
                    log(f'  {client}', 2)
                    return client
                else:
                    err = f'GET_DEVICE => No device found by filter `{key}={val}`.'
                    raise AttributeError(err)
            else:
                err = f'GET_DEVICE => No data received from the API.'
                raise RuntimeError(err)
        else:
            log(f'GET_DEVICE => Status code is not 200:', 0)
            log(f'  Status    => {res.status_code}', 0)
            log(f'  Response  => {res.text}', 0)
    else:
        err = f'WEB => Missing SessionTicket in cookie.'
        raise AttributeError(err)


def get_firewall_rule_ip(firewall_rule_name, config):
    """Fetches the IP address currently associated with the firewall rule.

        Parameters
        ----------
        firewall_rule_name : str
            The name of the firewall rule to fetch.

        config : obj
            The Altibox config to parse.

        Returns
        -------
        internal_ip : str
            A string containing the last part of the IP address.
    """
    routes = config.get('router').get('routes')
    rule = {key: val for key, val in routes.items() if val.get('name') == firewall_rule_name}
    if rule:
        rule = list(rule.values())[0]
        log(f'GET_RULE => Found rule (src=name:{firewall_rule_name}).', 2)
        log(f'  {rule}', 2)
        log(f'  {rule.get("type")}://{rule.get("ext_from")}-{rule.get("ext_to")} => X.X.X.{rule.get("int_ip")}:{rule.get("int_from")}-{rule.get("int_to")}', 2)
        internal_ip = rule.get('int_ip')

        return internal_ip
    else:
        err = f'GET_RULE => No rule found by filter `name={firewall_rule_name}`.'
        raise AttributeError(err)


def set_firewall_rule_ip(firewall_rule_name, ip, config):
    """Updates the IP address currently associated with the firewall rule.

        Parameters
        ----------
        firewall_rule_name : str
            The name of the firewall rule to fetch.

        ip : str
            The last part of the IP address to use.

        config : obj
            The Altibox config to parse.

        Returns
        -------
    """
    if COOKIE.get('sessionTicketApi') and HEADERS.get('SessionTicket'):
        url = BASE_URL + PATHS.get('fw')
        HEADERS['Referer'] = 'https://www.altibox.no/mine-sider/internett/min-hjemmesentral/'
        HEADERS['X-Requested-With'] = 'XMLHttpRequest'
        HEADERS['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        HEADERS['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        HEADERS['Origin'] = 'https://www.altibox.no'

        ip = ip.split('.')
        routes = config.get('router').get('routes')
        rules = {key: val for key, val in routes.items() if val.get('name') == firewall_rule_name}

        if rules:
            rule = list(rules.values())[0]
            log(f'SET_RULE => Found rule (src=name:{firewall_rule_name}).', 2)
            log(f'  {rule}', 2)
            log(f'  {rule.get("type")}://{rule.get("ext_from")}-{rule.get("ext_to")} => X.X.X.{rule.get("int_ip")}:{rule.get("int_from")}-{rule.get("int_to")}', 2)
            key = list(rules.keys())[0]
            routes[key]['int_ip'] = ip[3]
            config['router']['routes'] = routes

            payload = { 'data': prepare_config(config) }

            res = requests.post(url, headers=HEADERS, cookies=COOKIE, data=payload)

            if res.status_code == 200:
                data = res.json()
                if data:
                    if data.get('status') == 'success':
                        log(f'SET_RULE => Response from API: {data.get("message")}', 2)
                        data = data.get('data')
                        return list(data.values())[0]
                    else:
                        err = f'SET_RULE => An error occurred while updating the firewall.\n    Altibox: {data.get("message")}.'
                        raise RuntimeError(err)
                else:
                    err = f'SET_RULE => Error while updating the firewall rule IP: No response from the API.'
                    raise RuntimeError(err)
            else:
                log(f'SET_RULE => Status code is not 200:', 0)
                log(f'  Status    => {res.status_code}', 0)
                log(f'  Response  => {res.text}', 0)
        else:
            err = f'SET_RULE => No rule found by name `{firewall_rule_name}`.'
            raise AttributeError(err)
    else:
        err = f'WEB => Missing SessionTicket in cookie.'
        raise AttributeError(err)


def get_config():
    """Fetches the config from the Altibox API.

        Parameters
        ----------

        Returns
        -------
        config : obj
            An object representing the Altibox config.
    """
    if COOKIE.get('sessionTicketApi') and HEADERS.get('SessionTicket'):
        url = BASE_URL + PATHS.get('config') + '?siteid=2373251&_=1585046386097'
        HEADERS['Referer'] = 'https://www.altibox.no/mine-sider/internett/min-hjemmesentral/'
        HEADERS['X-Requested-With'] = 'XMLHttpRequest'

        res = requests.get(url, headers=HEADERS, cookies=COOKIE)

        if res.status_code == 200:
            data = res.json()
            if data:
                if data.get('status') == 'success':
                    data = data.get('data')
                    config = list(data.values())[0]

                    return config
                else:
                    err = f'GET_CONFIG => Altibox: {data.get("message")}.'
                    raise RuntimeError(err)
            else:
                err = f'GET_CONFIG => Error while fetching the config: No data received from the API.'
                raise RuntimeError(err)
        else:
            log(f'GET_CONFIG => Status code is not 200:', 0)
            log(f'  Status    => {res.status_code}', 0)
            log(f'  Response  => {res.text}', 0)
    else:
        err = f'WEB => Missing SessionTicket in cookie.'
        raise AttributeError(err)


def prepare_multi(multi):
    """Processes the formatted string and generates a list of rules to update.

        Parameters
        ----------
        multi : str
            A comma-separated string of devices and rules to update.
            Format:     `devicename|mac|rule`.
            Example:    `mediaserver||plex_rule,|4A:DA:61:1C:B5:24|vpn_rule`.

        Returns
        -------
    """
    if not ENTRIES:
        multi = multi.split(',')
        log(f'MULTI => Found {len(multi)} entries.', 2)
        for entry in multi:
            entry = entry.split('|')
            if len(entry) == 3:
                ENTRIES.append({
                    'hostname': entry[0],
                    'mac': entry[1],
                    'rule': entry[2]
                })
            else:
                log(f'MULTI => Entry {entry} does not follow the required format. Skipping.', 0)


def set_cookie(session, user):
    """Handles setting the cookie and headers required for authenticated requests.

        Parameters
        ----------
        session : str
            The SessionToken to use.

        user : obj
            The user object to use.

        Returns
        -------
    """
    if COOKIE:
        COOKIE['sessionTicketApi'] = session
        COOKIE['user'] = str(user)
    if HEADERS:
        HEADERS['SessionTicket'] = session


def run(hostname=None, mac=None, fw_rule=None):
    """Runs the script for updating a rule.

        Parameters
        ----------
        hostname : str
            The hostname of the device to fetch the IP of.

        mac : str
            The MAC address of the device to fetch the IP of.

        fw_rule : str
            The name of the firewall rule to update.

        Returns
        -------
    """
    try:
        if (hostname or mac) and fw_rule:
            session, user = authenticate()
            set_cookie(session, user)
            device = get_device(hostname=hostname, mac=mac)
            config = get_config()
            current_rule_ip = get_firewall_rule_ip(fw_rule, config)

            if device.get('ipAddress').split('.')[3] != current_rule_ip:
                log(f'Device IP ({device.get("ipAddress").split(".")[3]}) does not match rule IP ({current_rule_ip}). Updating..', 2)
                config = set_firewall_rule_ip(fw_rule, device.get('ipAddress'), config)
                current_rule_ip = get_firewall_rule_ip(fw_rule, config)
                if current_rule_ip == device.get('ipAddress').split('.')[3]:
                    log(f'RULE => Firewall rule `{fw_rule}` was updated successfully.', 2)
                    log(f'OK {fw_rule}', -1)
                else:
                    err = f'SET_RULE => The firewall rule IP was not updated properly.'
                    raise RuntimeError(err)
            else:
                log(f'SET_RULE => Firewall rule IP already up to date. Exiting.', 2)
                log(f'OK {fw_rule}', -1)
        else:
            missing = [val for val in [hostname, mac, fw_rule] if val is None]
            err = f'Missing attribute(s) `{missing}'
            raise AttributeError(err)
    except Exception as e:
        log(e, 0)
        sys.exit(2)


def main():
    if ENTRIES:
        log(f'MAIN => Updating rules for {len(ENTRIES)} entries.', 2)
        for entry in ENTRIES:
            log(f'MAIN => Running update for {entry.get("rule")}.', 2)
            run(hostname=entry.get('hostname'), mac=entry.get('mac'), fw_rule=entry.get('rule'))
        log(f'MAIN => Finished updating {len(ENTRIES)} entries.', 2)
        sys.exit(0)
    elif (HOSTNAME or MAC_ADDR) and FW_RULE:
        log(f'MAIN => Running update for {HOSTNAME}.', 2)
        run(hostname=HOSTNAME, mac=MAC_ADDR, fw_rule=FW_RULE)
        sys.exit(0)
    else:
        print(HELPMSG)
        log(f'MAIN => No targets found. Did you specify a target?', 0)
        sys.exit(2)

if __name__ == '__main__':
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, 'h:m:r:a:v:l:', ['hostname=', 'mac=', 'rule=', 'all', 'verbosity=', 'logpath=', 'help'])
    except getopt.GetoptError:
        print(HELPMSG)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '--help':
            print(HELPMSG)
            sys.exit(0)
        elif opt in ('-h', '--hostname'):
            HOSTNAME = arg
        elif opt in ('-m', '--mac'):
            MAC_ADDR = arg
        elif opt in ('-r', '--rule'):
            FW_RULE = arg
        elif opt in ('-v', '--verbosity'):
            if arg in VERBOSITY_MODES.values():
                level = {l: mode for l, mode in VERBOSITY_MODES.items() if mode == arg}
                VERBOSITY = list(level.keys())[0]
            else:
                log(f'LOGGER => Invalid mode for verbosity `{arg}`. Setting to default `INFO`.', 1)
                VERBOSITY = 1
        elif opt in ('-l', '--logpath'):
            if os.path.isdir(arg):
                LOGPATH = arg
                log(f'LOGGER => Logging to file enabled. Writing to `{LOGPATH}`.', 2)
            else:
                cwd = os.getcwd()
                log(f'LOGGER => Invalid path for logpath `{arg}`. Setting to default (CWD) `{cwd}`', 0)
        elif opt in('-a', '--all'):
            prepare_multi(arg)

    if ALL:
        prepare_multi(ALL)

    if ((HOSTNAME or MAC_ADDR) and FW_RULE) or ENTRIES:
        main()
    else:
        print(HELPMSG)
        log(f'Missing parameters. Please specify using either environment variables or CLI parameters.', 0)
        sys.exit(2)
