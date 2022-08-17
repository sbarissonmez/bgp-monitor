from jnpr.junos import Device
from jnpr.junos.op.routes import RouteTable
import sys
import datetime
import os
import smtplib
import socket

#################
# Required values
#################
deviceName = 'Juniper SRX'
deviceIP = 'x.x.x.x'
apiuser = 'username'
apipassword = 'password'
SMTP = 'smtp-alias'
fromName = 'BGP Monitor'
fromAddr = 'bgpmonitor@domain.com'
toName = 'contactName'
toAddr = 'contact@domain.com'
prefixDict = {
    "FriendlyName": "Prefix",
    "Route-to-Inet": "0.0.0.0/0"
}
#################


#################
# Other Stuff
#################
hostname = socket.gethostname()
logfile = "./bgp.log"
tempfile = "./bgproutes.temp"
timestamp = datetime.datetime.now()
#################


# Set device address/credentials
dev = Device(deviceIP, user=apiuser, password=apipassword)

# Function to send alert email


def sendMail(oldroutes, newroutes, status):
    message = """From: %s <%s>
To: %s <%s>
Subject: BGP Monitor - Change Detected

bgp-monitor.py has detected a change in learned BGP routes.

Please check BGP peers on %s (%s).

Previous Route List: %s
New Route List: %s

Status: %s

Alert generated at %s

SENT FROM %s
    """ % (fromName, fromAddr, toName, toAddr, deviceName, deviceIP,
           oldroutes, newroutes, status, timestamp, hostname)
    server = smtplib.SMTP(SMTP)
    server.sendmail(fromAddr, toAddr, message)

# Function to check received BGP routes


def checkBGP():
    with open(logfile, 'ab') as a:
        a.write("Running BGP Check Script at: %s \n" % timestamp)
    try:
        # Open SRX session
        dev.open()
        with open(logfile, 'ab') as a:
            a.write("Opened connection to %s \n" % deviceIP)
    except:
        with open(logfile, 'ab') as a:
            a.write("ERR: FAILED TO OPEN CONNECTION TO %s \n" % deviceIP)
        sys.exit(0)

    # Pull device routing table, then keep only BGP originated routes
    allroutes = RouteTable(dev)
    bgp = allroutes.get(protocol="bgp").keys()

    # Close SRX session
    dev.close()

    # Check for local temp file - if it doesn't exist, then assume first-run
    # and create file with data.
    if not os.path.isfile(tempfile):
        with open(tempfile, 'w+b') as a:
            a.write(str(bgp))
        sys.exit(0)

    # Local file used to keep track of BGP learned routes
    with open(tempfile, 'ab') as a:
        lastroutes = a.readlines()
        # Compare if routes are different
        if str(bgp) == str(lastroutes[0]):
            sys.exit(0)
        if str(bgp) != str(lastroutes[0]):
            pass
    # Delete file, then re-create with new route list
    #os.remove(tempfile)
    with open(tempfile, 'w+b') as a:
        a.write(str(bgp))

    # Create Status list, by checking received routes in bgp object
    status = []
    for name, prefix in prefixDict.items():
        if prefix in bgp:
            status.append("%s - RECEIVED" % name)
        if not prefix in bgp:
            status.append("%s - MISSING" % name)

    # Send alert message
    sendMail(str(lastroutes[0]), str(bgp), status)


if __name__ == '__main__':
    checkBGP()
