import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
import socket
import struct
import pickle
from datetime import datetime
from collections import OrderedDict

class HandlerClass(SimpleHTTPRequestHandler):
    def get_ip_address(self, ifname):
        # Ensure the use of Unix-specific code for fetching the IP address.
        # This will not work on Windows.
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])

    def log_message(self, format, *args):
        if len(args) < 3 or "200" not in args[1]:
            return
        try:
            with open("pickle_data.txt", "rb") as f:
                request = pickle.load(f)
        except (FileNotFoundError, EOFError):
            request = OrderedDict()
        time_now = datetime.now()
        ts = time_now.strftime('%Y-%m-%d %H:%M:%S')
        server = self.get_ip_address('eth0')
        host = self.address_string()
        addr_pair = (host, server)
        if addr_pair not in request:
            request[addr_pair] = [1, ts]
        else:
            num = request[addr_pair][0] + 1
            del request[addr_pair]
            request[addr_pair] = [num, ts]
        with open("index.html", "w") as file:
            file.write("<!DOCTYPE html> <html> <body><center><h1><font color=\"blue\" face=\"Georgia, Arial\" size=8><em>Real</em></font> Visit Results</h1></center>")
            for pair in request:
                if pair[0] == host:
                    guest = "LOCAL: " + pair[0]
                else:
                    guest = pair[0]
                if (time_now - datetime.strptime(request[pair][1], '%Y-%m-%d %H:%M:%S')).seconds < 3:
                    file.write("<p style=\"font-size:150%\" >#"+ str(request[pair][1]) +": <font color=\"red\">"+str(request[pair][0])+ "</font> requests " + "from &lt<font color=\"blue\">"+guest+"</font>&gt to WebServer &lt<font color=\"blue\">"+pair[1]+"</font>&gt</p>")
                else:
                    file.write("<p style=\"font-size:150%\" >#"+ str(request[pair][1]) +": <font color=\"maroon\">"+str(request[pair][0])+ "</font> requests " + "from &lt<font color=\"navy\">"+guest+"</font>&gt to WebServer &lt<font color=\"navy\">"+pair[1]+"</font>&gt</p>")
            file.write("</body> </html>")
        with open("pickle_data.txt", "wb") as f:
            pickle.dump(request, f)

if __name__ == '__main__':
    try:
        ServerClass = HTTPServer
        Protocol = "HTTP/1.0"
        addr = len(sys.argv) < 2 and "0.0.0.0" or sys.argv[1]
        port = len(sys.argv) < 3 and 8000 or int(sys.argv[2])
        HandlerClass.protocol_version = Protocol
        httpd = ServerClass((addr, port), HandlerClass)
        sa = httpd.socket.getsockname()
        print("Serving HTTP on", sa[0], "port", sa[1], "...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.socket.close()
    except Exception as e:
        print(f"Error: {e}")
