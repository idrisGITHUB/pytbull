#!/usr/bin/env python
#
# Pytbull is an IDS/IPS testing framework for Snort & Suricata
# It is shipped with 300 tests grouped in 9 testing modules
#
# Pytbull has been developed by Sebastien Damaye
# sebastien #dot# damaye #at# gmail #dot# com

import socket
import time
from ftplib import FTP
from scapy.all import *
import subprocess
import os
import os.path
import sys
import datetime

import testRules
import badTraffic
import fragmentedPackets
import multipleFailedLogins
import evasionTechniques
import malwaresViruses
import shellCodes
import dos
import clientSideAttacks

class Pytbull():
    def __init__(self, target, idstype):
        # Check if prgm is called with root privs
        # Needed for generating raw packets (e.g. some nmap scans)
        if(os.getuid() != 0):
            print "Root privileges required!"
            sys.exit(0)

        # Params
        self._final     = "./report.html"
        self._ftpuser   = "pilou"
        self._ftppasswd = "oops"
        self._sudo      = "/usr/bin/sudo"
        self._nmap      = "/usr/bin/nmap"
        self._niktopath = "/pentest/scanners/nikto-2.1.4/"

        # Tests selection (False|True)
        self.testRules              = True
        self.badTraffic             = True
        self.fragmentedPackets      = True
        self.multipleFailedLogins   = False
        self.evasionTechniques      = True
        self.malwaresViruses        = False
        self.shellCodes             = True
        self.dos                    = True
        self.clientSideAttacks      = False

        # Vars initialization
        self._target    = target
        self._idstype   = idstype
        self.testnum    = 1
        self.report     = "/tmp/pytbull.tmp"
        self._niktobin  = os.path.join(self._niktopath, "nikto.pl")
        self._niktocnf  = os.path.join(self._niktopath, "nikto.conf")

        # Remove temp file
        if os.path.exists("/tmp/pytbull.tmp"):
            os.remove("/tmp/pytbull.tmp")

        # Chek if paths are valid
        # ...to be completed...
        
    def testRules(self):
        payloads = TestRules(self._target).getPayloas()
        tests(payloads)

    def doTest(self, payloads):
        for payload in payloads:
            # Perform test & write report
            print " - %s" % payload[0]
            content  = """<table border="1">"""
            content += """<tr><th>Test num</th><td>%s</td></tr>""" % self.testnum
            self.testnum += 1
            content += """<tr><th>Time</th><td>%s</td></tr>""" % datetime.datetime.now()
            content += """<tr><th>Test name</th><td>%s</td></tr>""" % payload[0]

            if payload[1] == "socket":
                content += """<tr><th>Port</th><td>%s/tcp</td></tr>""" % payload[2]
                content += """<tr><th style="vertical-align:top">Payload</th><td><textarea style="width:800px;height:60px;">%s</textarea></td></tr>""" % payload[3]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self._target,payload[2]))
                s.send(payload[3])
                s.close()
            elif payload[1] == "command":
                content += """<tr><th style="vertical-align:top">Payload</th><td><textarea style="width:800px;height:60px;">%s</textarea></td></tr>""" % ' '.join(payload[2])
                subprocess.call(payload[2])
            elif payload[1] == "scapy":
                content += """<tr><th style="vertical-align:top">Payload</th><td><textarea style="width:800px;height:60px;">%s</textarea></td></tr>""" % payload[2]
                eval(payload[2])

            # Sleep 10 seconds before getting alerts
            time.sleep(10)

            # Get new alerts and calculate new offset
            self.getAlertsFile(self._idstype)
            res = self.getAlertsFromOffset(self.report, self.offset)
            content += """<tr><th style="vertical-align:top">Alerts</th><td><textarea style="width:800px;height:200px;">%s</textarea></td></tr>""" % res
            self.offset = self.getOffset(self.report)

            content += """</table><br />"""
            self.writeReport(content)

            # Sleep 10 second before next test
            time.sleep(10)

    def doAllTests(self):
        # Initialize report
        self.initializeReport()

        # Initial offset
        self.getAlertsFile(self._idstype)
        self.offset = self.getOffset(self.report)

        # Do all tests

        if self.testRules:
            self.writeReport("""<h2 id="test-rules">Test Rules</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nTest rules"
            self.doTest( testRules.TestRules(self._target).getPayloads() )

        if self.badTraffic:
            self.writeReport("""<h2 id="bad-traffic">Bad Traffic</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nBad Traffic"
            self.doTest( badTraffic.BadTraffic(self._target).getPayloads() )

        if self.fragmentedPackets:
            self.writeReport("""<h2 id="fragmented-packets">Fragmented Packets</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nFragmented Packets"
            self.doTest( fragmentedPackets.FragmentedPackets(self._target).getPayloads() )

        if self.multipleFailedLogins:
            self.writeReport("""<h2 id="multiple-failed-logins">Multiple Failed Logins</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nMultiple Failed Logins"
            self.doTest( multipleFailedLogins.MultipleFailedLogins(self._target).getPayloads() )

        if self.evasionTechniques:
            self.writeReport("""<h2 id="evasion-techniques">Evasion Techniques</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nEvasion Techniques"
            self.doTest( evasionTechniques.EvasionTechniques(self._target).getPayloads() )

        if self.malwaresViruses:
            self.writeReport("""<h2 id="malwares-viruses">Malwares & Viruses</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nMalwares & Viruses"
            self.doTest( malwaresViruses.MalwaresViruses(self._target).getPayloads() )

        if self.shellCodes:
            self.writeReport("""<h2 id="shellcodes">ShellCodes</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nShellcodes"
            self.doTest( shellCodes.ShellCodes(self._target).getPayloads() )

        if self.dos:
            self.writeReport("""<h2 id="dos">Denial of Service</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nDoS"
            self.doTest( dos.Dos(self._target).getPayloads() )

        if self.clientSideAttacks:
            self.writeReport("""<h2 id="client-side-attacks">Client Side Attacks</h2><p>[<a href="#">top</a>]</p>""")
            print "~~~~~~~~~~~\nClient Side Attacks"
            self.doTest( clientSideAttacks.ClientSideAttacks(self._target).getPayloads() )

        # Finalize report
        self.finalizeReport()

        # Done!
        print "\n\n----------------"
        print "DONE!"
        print "----------------\n"

    def getAlertsFile(self, idstype):
        """Get the alerts file (FTP) from a remote Snort or Suricata server
        and save it to /tmp/pytbull.tmp"""
        # FTP Connection
        ftp = FTP(self._target)
        ftp.login(self._ftpuser, self._ftppasswd)
        # Get file
        f = open(self.report, "w")
        if idstype == "snort":
            alertsFile = "/var/log/snort/alert"
        else:
            alertsFile = "/var/log/suricata/access.log"
        ftp.retrbinary("RETR %s" % alertsFile, f.write)
        f.close()
        #Close FTP connection
        ftp.quit()

    def getOffset(self, report):
        """Get initial offset (Number of lines in alert file)"""
        f = open(report, "r")
        offset = len(f.readlines())
        f.close()
        return offset

    def getAlertsFromOffset(self, report, offset):
        f = open(report, "r")
        c = f.readlines()
        return ''.join(c[offset:])

    def initializeReport(self):
        """Open a report (HTML file) and initialize it with HTML headers"""
        self.finalReport = open(self._final, 'w')
        self.writeReport( "<html><head><title>Detection Report</title></head><body>" )
        self.writeReport( "<h1>Detection Report - %s</h1>" % self._target )
        self.writeReport("""
            <ul>
            <li><a href="#test-rules">Test Rules</a></li>
            <li><a href="#bad-traffic">Bad Traffic</a></li>
            <li><a href="#fragmented-packets">Fragmented Packets</a></li>
            <li><a href="#multiple-failed-logins">Multiple Failed Logins</a></li>
            <li><a href="#evasion-techniques">Evasion Techniques</a></li>
            <li><a href="#malwares-viruses">Malwares & Viruses</a></li>
            <li><a href="#shellcodes">ShellCodes</a></li>
            <li><a href="#dos">Denial of Service</a></li>
            <li><a href="#client-side-attacks">Client Side Attacks</a></li>
            </ul><hr />
        """)

    def writeReport(self, content):
        """ Add content to HTML report """
        self.finalReport.write( content )

    def finalizeReport(self):
        """ Write end of report and close file """
        self.writeReport( "</body></html>" )
        self.finalReport.close()

if __name__ == '__main__':
    # Instantiate Pytbull class
    oPytbull = Pytbull("192.168.100.48", "snort")
    # Do all tests
    oPytbull.doAllTests()
    # Destruct object
    del oPytbull