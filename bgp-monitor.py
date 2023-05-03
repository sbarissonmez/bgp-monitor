from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
import sys
import datetime
import os
import smtplib
import socket

deviceName = 'Juniper SRX'
deviceIP = 'x.x.x.x'
apiuser = 'username'
apipassword = 'password'
SMTP = 'smtp-alias'
fromName = 'BGP Monitor'
fromAddr = 'bgpmonitor@company.com'
toName = 'networkAdmin'
toAddr = 'network@company.com'
prefixDict = {
    "FriendlyName": "Prefix",
    "Route-to-Inet": "0.0.0.0/0"
}

hostname = socket.gethostname()
logfile = "./bgp.log"
tempfile = "./bgproutes.temp"
timestamp = datetime.datetime.now()

dev = Device(deviceIP, user=apiuser, password=apipassword)

def sendMail(oldroutes, newroutes, status):
    message = """From: %s <%s>
To: %s <%s>
Subject: Change Detected by BGP Monitor

The script bgp-monitor.py has detected a change in the BGP routes being learned.

Please verify BGP peers on %s (%s).

Earlier Route List: %s
Updated Route List: %s

Status: %s

Alert triggered at %s

SENT FROM %s
    """ % (fromName, fromAddr, toName, toAddr, deviceName, deviceIP,
           oldroutes, newroutes, status, timestamp, hostname)
    server = smtplib.SMTP(SMTP)
    server.sendmail(fromAddr, toAddr, message)


def checkBGP():
    with open(logfile, 'ab') as a:
        a.write("Running BGP Monitor Script at: %s \n" % timestamp)
    try:
        dev.open()
        with open(logfile, 'ab') as a:
            a.write("Connected to %s \n" % deviceIP)
    except:
        with open(logfile, 'ab') as a:
            a.write("ERR: FAILED TO CONNECTION TO %s \n" % deviceIP)
        sys.exit(0)

    allroutes = RouteTable(dev)
    bgp = allroutes.get(protocol="bgp").keys()
    dev.close()

    if not os.path.isfile(tempfile):
        with open(tempfile, 'w+b') as a:
            a.write(str(bgp))
        sys.exit(0)

    with open(tempfile, 'ab') as a:
        lastroutes = a.readlines()
        if str(bgp) == str(lastroutes[0]):
            sys.exit(0)
        if str(bgp) != str(lastroutes[0]):
            pass

    with open(tempfile, 'w+b') as a:
        a.write(str(bgp))

    status = []
    for name, prefix in prefixDict.items():
        if prefix in bgp:
            status.append("%s - RECEIVED" % name)
        if not prefix in bgp:
            status.append("%s - MISSING" % name)

    sendMail(str(lastroutes[0]), str(bgp), status)

if __name__ == '__main__':
    checkBGP()
