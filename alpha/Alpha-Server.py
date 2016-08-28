#!/usr/bin/env python3

# Specifications :
#       1 per Cluster/Network

import http.server
import socketserver
import signal
import urllib.request

import sys, os, re
import cgi

# ==========================
#   Import lambdaUtils
# ==========================
filePath=os.path.abspath(os.path.join(os.path.dirname(__file__)))
rootPath=os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(rootPath)
import lambdaUtils as lu
os.chdir(filePath)

# ==========================
#   Global Defaults
# ==========================
port=lu.ports["alpha"]
addr=lu.getAddr()
codeDir = "codeScrolls"

# ==========================
#   Parse Args
# ==========================
args=sys.argv[1:]
for i in range(len(args)):
    if (args[i] == "-p"):
        port = int(args[i+1])
    if (args[i] == "-a"):
        addr = str(args[i+1])

# ==========================
#   Init Setup
# ==========================
if not os.path.exists(codeDir):
    os.makedirs(codeDir)

# ==========================
#   Main user front end server
# ==========================
addr=lu.getAddr()
OmegaAddr=lu.getOmegaAddr(addr)
class handler(http.server.BaseHTTPRequestHandler):
    # set http headers
    def setHeaders(self, code):
        self.send_response(code)
        self.send_header(b'Content-type', 'text/html')
        self.end_headers()
    def writeDataToHandler(self, readFile):
        f = open(readFile, 'rb')
        bufferSize=50
        try:
            data = f.read(bufferSize)
            while (len(data) > 0):
                self.wfile.write(data)
                data = f.read(bufferSize)
        finally:
            f.close()
    # GET
    def do_GET(self): # check if contained to directory
        lu.log("Get Request - " + self.path)
        filePath=re.sub("^/",os.getcwd()+"/",self.path)
        filePath=re.sub("%20"," ",filePath)
        filePath=re.sub("/+","/",filePath)
        if (self.path == lu.paths["alpha_nodeListing"]): # node
            self.setHeaders(200)
            requestURL='http://'+str(OmegaAddr)+':'+str(lu.ports["omega"])+lu.paths["omega_TableJSON"]
            lu.log("Requesting " + requestURL)
            msg=None
            with urllib.request.urlopen(requestURL) as response:
                msg = response.read().decode("UTF-8")
            self.wfile.write(msg.encode("UTF-8"))
        elif os.path.isfile(filePath):
            self.setHeaders(200)
            self.writeDataToHandler(filePath)
        elif os.path.isdir(filePath):
            index=os.path.join(filePath,"index.html")
            if os.path.isfile(index):
                self.setHeaders(200)
                self.writeDataToHandler(index)
            else:
                if(len(os.listdir(filePath))):
                    for i in os.listdir(filePath):
                        i = "<a href=\'" + self.path + "/" + i + "\'>"+i+"</a></br>"
                        self.wfile.write(i.encode("UTF-8"))
                else:
                    self.wfile.write("directory empty".encode("UTF-8"))
        elif not os.path.exists(filePath):
            self.setHeaders(404)
            string="File : '" + filePath + "' not found."
            lu.log(string)
            self.wfile.write(string.encode("UTF-8"))
        else:
            self.setHeaders(500)
    # POST
    def do_POST(self):
        lu.log("Post Request - " + self.path)
        fp=self.rfile
        filePath=re.sub("^/",os.getcwd()+"/",self.path)
        filePath=re.sub("%20"," ",filePath)
        length = int(self.headers.get_all('content-length')[0])
        self.setHeaders(200)
        if(length > 0):
            f = open(filePath, 'wb')
            f.write(fp.read(length))
            f.close()
    # redirects a client using javascript
    def redirect(self, dest):
        html1='''
            <!DOCTYPE HTML>
            <html lang="en-US">
             <head>
                <meta charset="UTF-8">
                <script type="text/javascript">
                     window.location = " '''
        html2=''' ";
                 </script>
            </head>
            </html>
        '''
        html = html1 + dest + html2
        self.wfile.write(html.encode("UTF-8"))
    # deletes a script
    def do_DELETE(self):
        lu.log("Delete Request - " + self.path)
        self._setHeaders()
        self.wfile.write(b"<html><body><h1>delete!</h1></body></html>")

# ==========================
#   Iniitialize
# ==========================
try:
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer((addr, port), handler)
    broadcastListener = lu.nodeDiscovery("alpha")
    lu.log(" Serving @ " + str(addr) + ":" + str(port))
    httpd.serve_forever()
except OSError:
    lu.error("Port in use - " + str(port))
except KeyboardInterrupt:
    sys.exit(0)
