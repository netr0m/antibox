![Docker Stars Shield](https://img.shields.io/docker/stars/mortea15/antibox.svg?style=flat-square)
![Docker Pulls Shield](https://img.shields.io/docker/pulls/mortea15/antibox.svg?style=flat-square)
[![GitHub license](https://img.shields.io/badge/license-wtfpl-blue.svg?style=flat-square)](https://raw.githubusercontent.com/mortea15/antibox/master/LICENSE)

# Antibox
*A CLI tool to update [Altibox](https://www.altibox.no) firewall settings*

*Antibox* lets you automatically update the IP address associated with a firewall rule in your Altibox gateway. As Altibox has a maximum lease of 48h, and does not allow for static IPs, this script will help you avoid port forwarding issues when the lease expires.

## Installation
1. Optional: Create a virtual environment
    ```bash
    $ pip3 install virtualenv
    $ virtualenv .env
    $ source .env/bin/activate
    ```
2. Install dependencies
    ```bash
    $ pip3 install -r requirements.txt
    ```
3. Copy, edit and source env vars
    ```bash
    # Bash
    cp vars.env.example vars.env
    vim vars.env
    source vars.env
    # Docker
    $ cp list.env.example list.env
    $ vim list.env
    ```

## Usage
### CLI
```bash
$ python3 antibox.py --help
antibox v0.2.0
usage: antibox (-h <HOSTNAME> | -m <MAC_ADDRESS>) -r <RULE_NAME> [-v <(ERROR|INFO|DEBUG)>] [-l <PATH>] [--help]

    Get current IP of device
      -h, --hostname          By hostname
      -m, --mac               By MAC address

      -r, --rule              Name of the rule to modify

      -v, --verbosity         Set the verbosity.
                                Available options: [ERROR, INFO, DEBUG]
      -l, --logpath           Path to the directory for log files

      --help                  Print this message
```

```bash
# Set the internal IP of the firewall rule `rule` to the IP of device `hostname`
$ python3 antibox.py -h <hostname> -r <rule>
# Same, but with the MAC address of the device
$ python3 antibox.py -m <mac> -r <rule>

# Change the verbosity
$ python3 antibox.py -h <hostname> -r <rule> -v DEBUG

# Log to file
$ python3 antibox.py -h <hostname> -r <rule> -v DEBUG -l /path/to/dir

# Get hostname/MAC and rule from environment variables:
$ source vars.env
$ python3 antibox.py
```

#### Schedule using cron
[crontab guru](https://crontab.guru/)
1. **Every 10th minute:** */10 * * * *
2. **Every day at 1 AM:** 0 1 * * *
```bash
$ chmod a+x antibox.py
$ crontab -e
# Run every 10th minute, on-host:
$ */10 * * * * /usr/local/bin/python <path_to_dir>/antibox.py
# Run every day at 1 AM, containerized:
$ 0 1 * * * docker run --rm -d --name antibox --env-file list.env mortea15/antibox
```

### Docker
**Runs the script in a Docker container for a one-time execution**
```bash
# Get params from the file `list.env`
$ docker run --rm -d --name antibox --env-file list.env mortea15/antibox
# Add CLI params
$ docker run --rm -d --name antibox --env-file list.env mortea15/antibox python antibox.py -v DEBUG
# Use CLI params only, no env file.
$ docker run --rm -d --name antibox mortea15/antibox python antibox.py -h <HOSTNAME> -r <RULE> -v DEBUG -l /var/log
# Run using the [docker-compose.yml](/docker-compose.yml) file
$ docker-compose up -d
```

#### Cron in Docker
**Runs a Docker container pre-configured with Cron**
- Executes the script every 10th minute
- Requires environment variables to be provided using `list.env` (see [list.env.example](/list.env.example))
```bash
$ docker run --rm -d --name antibox --env-file list.env mortea15/antibox:cron
```

#### Build the images from source
**Antibox**
- [Dockerfile](/Dockerfile)
```bash
$ docker build -t antibox .
```

**With Cron**
- [Dockerfile](/Dockerfile.cron)

*If you wish to change the frequency, modify the file [crontab](/crontab) before building.*
```bash
$ docker build -t antibox:cron -f Dockerfile.cron .
```

## Additional
### Environment variables
- **ALTIBOX_USER:** Username/email for your Altibox account
- **ALTIBOX_PASS:** Password
- **DEVICE_NAME:**  Name of the device to fetch the IP of
- **DEVICE_MAC:**   MAC of the device to fetch the IP of
- **RULE_NAME:**    Name of the firewall rule to modify
- **VERBOSITY:**    Set the verbosity [ERROR, INFO, DEBUG]
- **LOGPATH:**      Specify a directory to write logfiles to    