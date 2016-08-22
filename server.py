import http.server
import socketserver
import select
import traceback
import socket

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
	pass

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
	protocol_version = 'HTTP/1.1'

	def do_CONNECT(self):
		address = self.path.split(':', 1)
		address[1] = int(address[1]) or 443

		self.log_request()

		try:
			s = socket.create_connection(address, timeout=self.timeout)
		except Exception:
			traceback.print_exc()
			self.send_error(502)
			return

		self.send_response(200, 'Connection Established')
		self.end_headers()

		conns = [self.connection, s]
		self.close_connection = 0
		while not self.close_connection:
			rlist, wlist, xlist = select.select(conns, [], conns, self.timeout)
			if xlist or not rlist:
				break
			for r in rlist:
				other = conns[1] if r is conns[0] else conns[0]
				data = r.recv(8192)
				if not data:
					self.close_connection = 1
					break
				other.sendall(data)
		
		return

BIND_ADDRESS = ('', 8889)
httpd = ThreadedHTTPServer(BIND_ADDRESS, ProxyRequestHandler)

print('Server is running at {}'.format(':'.join(map(str,BIND_ADDRESS))))
httpd.serve_forever()
