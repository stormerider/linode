#!/usr/bin/env python3
#
# Easy Python3 Dynamic DNS
# By Jed Smith <jed@jedsmith.org> 4/29/2009
# This code and associated documentation is released into the public domain.
#
# This script **REQUIRES** Python 3.0 or above.  Python 2.6 may work.
# To see what version you are using, run this:
#
#   python --version
#
# For automated processing, this script will always print EXACTLY one line, and
# will also communicate via a return code.  The return codes are:
#
#   -1 - Error loading configuration
#    0 - No need to update, A record matches my public IP
#    1 - Updated record
#    2 - Some kind of error or exception occurred
#
# The script will also output one line that starts with either OK or FAIL.  If
# an update was necessary, OK will have extra information after it.
#
# If you want to see responses for troubleshooting, set this:
#
DEBUG = False

#####################
# STOP EDITING HERE #

try:
    from json import load
    from urllib.parse import urlencode
    from urllib.request import urlretrieve
    import configparser
    import os
except Exception as excp:
    exit("Couldn't import the standard library. Are you running Python 3?")

def execute(action, parameters):
    global API, KEY

    api = API.format(KEY)
    if DEBUG:
        print("--> API = ", api)
    # Execute a query and return a Python dictionary.
    uri = "{0}&action={1}".format(api, action)
    if parameters and len(parameters) > 0:
        uri = "{0}&{1}".format(uri, urlencode(parameters))
    if DEBUG:
        print("-->", uri)
    file, headers = urlretrieve(uri)
    if DEBUG:
        print("<--", file)
        print(headers, end="")
        print(open(file).read())
        print()
    json = load(open(file), encoding="utf-8")
    if len(json["ERRORARRAY"]) > 0:
        err = json["ERRORARRAY"][0]
        raise Exception("API Error {0}: {1}".format(int(err["ERRORCODE"]),
            err["ERRORMESSAGE"]))
    return json

def ip():
    global GETIP

    if DEBUG:
        print("--> ip: ", GETIP)
    file, headers = urlretrieve(GETIP)
    if DEBUG:
        print("<--", file)
        print(headers, end="")
        print(open(file).read())
        print()
    return open(file).read().strip()

def configure_this():
    conf = configparser.ConfigParser()
    conf.read(['/etc/linode/linode.conf', os.path.expanduser('./linode.conf')])
    return (conf)

def main():
    global API, KEY, RESOURCE, DOMAINID, GETIP

    conf = configure_this()
    general = conf['general']

    DOMAINID = general.get('domainid')
    RESOURCE = general.get('resource')
    GETIP = general.get('getip', 'http://hosted.jedsmith.org/ip.php')
    KEY = general.get('key')
    API = general.get('api', "https://api.linode.com/api/?api_key={0}&resultFormat=JSON")

    if RESOURCE == '000000':
        print("You must customize the values in linode.conf")
        return -1

    try:
        res = execute("domainResourceGet", {"ResourceID": RESOURCE, "DomainID": DOMAINID})["DATA"][0]
        if(len(res)) == 0:
            raise Exception("No such resource?".format(RESOURCE))
        public = ip()
        if DEBUG:
            print("New Public IP:", public)
            print("Old Public IP:", res["TARGET"])

        if res["TARGET"] != public:
            old = res["TARGET"]
            request = {
                "ResourceID": res["RESOURCEID"],
                "DomainID": res["DOMAINID"],
                "Name": res["NAME"],
                "Type": res["TYPE"],
                "Target": public,
                "TTL_Sec": res["TTL_SEC"]
            }
            execute("domainResourceSave", request)
            print("OK {0} -> {1}".format(old, public))
            return 1
        else:
            print("OK - no update needed")
            return 0
    except Exception as excp:
        print("FAIL {0}: {1}".format(type(excp).__name__, excp))
        return 2

if __name__ == "__main__":
    global API, KEY, RESOURCE, DOMAINID, GETIP
    exit(main())
