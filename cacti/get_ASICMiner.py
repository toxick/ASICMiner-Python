#!/usr/bin/python 

import requests, re, socket, argparse, sys

def parseArgs():

  parser = argparse.ArgumentParser(description="Tool to pull cacti stats out of ASICMiner Blades (v2)")
  parser.add_argument("--host",  metavar="<host>", help="Target Blade IP", required=True)
  parser.add_argument("--port",  metavar="<port>", help="Target Blade Web Port", required=True)
  parser.add_argument("--items", metavar="xx,xx,..", help="List of items, comma separated", required=True)

  return parser.parse_args()

def main():
  args = parseArgs()
  x = ''

  ################################################3
  #
  # Fire in the hole
  #
  try:
    hostPort = "%s:%s" % (args.host, args.port)
    x = Blade(hostPort)
  except BladeError, err:
    print "[%s] Error: %s" % (args.host, err.msg)
  else:
    validItems = { "mh" : x.MHPS, "rc" : x.received , "ac" : x.accepted, "pm" : x.perMinute, "ch" : x.chipHealth.count("O"), "ut": "%0.2f" % x.uptime }
    pad = ''

    for item in args.items.split(","):
      if item in validItems:
        sys.stdout.write("%s%s:%s" % (pad, item, validItems[item]))
        pad = ' '

class BladeError(Exception):
  def __init__(self, value):
    self.msg = value
  def __str__(self):
    return self.msg

class Blade():

  def __init__(self, URL):

    self.URL = URL
    self.currentServer = ''
    self.MHPS = ''
    self.chipHealth = ''
    self.received = ''
    self.accepted = ''
    self.perMinute = ''
    self.efficiency = 0.0
    self.uptime = 0.0
    self.address = ''
    self.netmask = ''
    self.gateway = ''
    self.webport = ''
    self.pdns    = ''
    self.sdns    = ''
    self.phost   = ''
    self.shost   = ''
    self.pport   = ''
    self.sport   = ''
    self.puser  = ''
    self.suser  = ''
    self.request = ''
    self.form    = {}

    try:
      self.update()
    except BladeError:
      raise

    return

  def update(self):
    try:
      self.request = self.query("Main")
    except BladeError:
      raise

    m = re.search("Current Server:\s*([0-9\.:]+?)<", self.request.content)
    try:
      self.currentServer = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.currentServer = "X"

    m = re.search("Total MHS:</td><td align=\'left\'>([0-9]+)", self.request.content)
    try:
      self.MHPS = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.MHPS = "X"

    m = re.search("Received:</td><td align=\'left\'>([0-9]+)", self.request.content)
    try:
      self.received = m.groups()[0].lstrip("0")
    except (TypeError, ValueError, AttributeError):
      self.received = "X"

    m = re.search("Per Minute:</td><td align=\'left\'>([0-9.]+)", self.request.content)
    try:
      self.perMinute = m.groups()[0].lstrip("0")
    except (TypeError, ValueError, AttributeError):
      self.perMinute = "X"

    m = re.search("Up Time:</td><td align=\'left\'>([\S]+?)<", self.request.content)
    uptime = ''
    try:
      uptime = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.uptime = 0
    else:
      for part in uptime.split(","):
        key   = part[len(part)-1]
        value = int(part.rstrip("dhms"))

        if key == "d":
          self.uptime += (86400 * value)

        if key == "h":
          self.uptime += 3600 * value

        if key == "m":
          self.uptime += 60 * value

        if key == "s":
          self.uptime += value

      self.uptime = float(self.uptime / 86400)

    m = re.search("Accepted:</td><td align=\'left\'>([0-9]+)", self.request.content)
    try:
      self.accepted = m.groups()[0].lstrip("0")
    except (TypeError, ValueError, AttributeError):
      self.accepted = "X"

    m = re.search("Chip: ([OX]+)", self.request.content)
    try:
      self.chipHealth = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.chipHealth = "X"

    m = re.search("input name=JMIP value='(.*?)'", self.request.content)
    try:
      self.form["JMIP"] = m.groups()[0]
      self.form["JMIP"] = self.address = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.address = 'X'

    m = re.search("input name=JMSK value='(.*?)'", self.request.content)
    try:
      self.form["JMSK"] = self.netmask = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.netmask = 'X'

    m = re.search("input name=JGTW value='(.*?)'", self.request.content)
    try:
      self.form["JGTW"] = self.gateway = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.gateway = 'X'

    m = re.search("input name=WPRT value='(.*?)'", self.request.content)
    try:
      self.form["WPRT"] = self.webport = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.webport = 'X'

    m = re.search("input name=PDNS value='(.*?)'", self.request.content)
    try:
      self.form["PDNS"] = self.pdns = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.pdns = 'X'

    m = re.search("input name=SDNS value='(.*?)'", self.request.content)
    try:
      self.form["SDNS"] = self.sdns = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.sdns = 'X'

    m = re.search("input name=MPRT value='(.*?)'", self.request.content)
    try:
      self.pport, self.sport = m.groups()[0].split(",")
      self.form["MPRT"] = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.pport = self.sport = 'X'

    m = re.search("input name=MURL value='(.*?)'", self.request.content)
    try:
      self.phost, self.shost = m.groups()[0].split(",")
      self.form["MURL"] = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.phost = self.shost = 'X'

    m = re.search("input name=USPA value='(.*?)'", self.request.content)
    try:
      self.puser, self.suser = m.groups()[0].split(",")
      self.form["USPA"] = m.groups()[0]
    except (TypeError, ValueError, AttributeError):
      self.pdns = 'X'

    self.efficiency = ( float(self.accepted) / float(self.received) ) * 100
    self.form["update"] = "Update/Restart"

    return 

  def switchServer(self):
    try:
      self.query("Sw_Pool")
    except BladeError:
      raise

  def uploadRestart(self):
    try:
      result = self.query("Upload_Data", post=self.form, timeout=10)
    except BladeError:
      raise

    return result

  def query(self, path, timeout=3, post=None):
    result = None
    try:
      URL = "http://%s/%s" % (self.URL, path)
      if post:
        result = requests.post(URL, timeout=timeout, data=post)
      else:
        result = requests.get(URL, timeout=timeout)
    except requests.ConnectionError, err:
      raise BladeError("Could not connect to web port: %s" % err.message)
    except requests.HTTPError, err:
      raise BladeError("Invalid HTTP Response: %s" % err.message)
    except (requests.Timeout, socket.timeout), err:
      if timeout == 3:
        self.query(path, timeout=5, post=post)
      else:
        raise BladeError("Timed out connecting")

    return result

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print "CTRL-C"

