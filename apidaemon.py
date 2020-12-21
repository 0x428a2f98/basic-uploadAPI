"""
implements APIDaemon that runs HTTPServer that handles post
api requests in the background.

doesn't support anything but start/restart/status(runing or not)/stop
"""

import sys
import time
import importlib
from http.server import HTTPServer

from genericdaemon import Daemon
import uploadapi


class APIDaemon(Daemon):
    """Basic implementation provided by an original base daemon class author with
    run() method that setups and starts HTTPServer

    Attributes:
        port : port to serve requests on.
        address : address to serve requests on.
    """
    def __init__(self, pidfile):
        """Adds port and address attributes to APIDaemon instance.
        """        
        super().__init__(pidfile) 
        self.port = "4040"
        self.address = "localhost"

    def run(self):
        """Inits HTTPServer with a custom upload api http request handler implemented
        in <uploadapi>.
        """
        importlib.reload(uploadapi)
        Handler = uploadapi.UploadAPIHandler

        httpd = HTTPServer((self.address, int(self.port)), Handler)
        httpd.serve_forever()
        while True:
            time.sleep(1)

    def status(self):
        """Prints out daemon debug info. Only available information is if daemon's active or not.
        TO_DO
        """
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())

        except IOError:
            pid = None

        if pid:
            message = "UploadAPI daemon running.\n"
            message += "Servicing api requests on: " + self.address + ":" + self.port + "\n"
            sys.stderr.write(message.format(self.pidfile))
        else:
            message = "UploadAPI daemon not running.\n"
            sys.stderr.write(message.format(self.pidfile))


if __name__ == "__main__":
    daemon = APIDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start' :
            daemon.start()
        elif sys.argv[1] == 'status':
            daemon.status()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|status|stop|restart" % sys.argv[0])
        sys.exit(2)
