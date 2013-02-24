from __future__ import print_function, absolute_import, unicode_literals, division
from runnable.runnable import Runnable
import socket, select

class RequestObject(object):
	def __init__(self, conn):
		self.conn = conn

	def init(self):
		pass

	def destroy(self):
		pass

	def receive(self):
		pass

class RunnableServerError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

class RunnableServer(Runnable):
	def execute(self):
		port = self.properties['port']
		reqObj = self.properties['reqObj']
		if not issubclass(reqObj, RequestObject):
			raise RunnableServerError('reqObj not subclass of RequestObject')

		servsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		servsock.setblocking(0)
		servsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		servsock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		servsock.settimeout(None)

		servfdmap = {servsock.fileno(): servsock}
		clients = {}

		servpoll = select.poll()
		pollin, pollpri, pollhup, pollerr = select.POLLIN, select.POLLPRI, select.POLLHUP, select.POLLERR

		def terminate(fd):
			clients[fd].destroy()
			servpoll.unregister(servfdmap[fd])
			del clients[fd]
			del servfdmap[fd]

		servsock.bind(("0.0.0.0", port))
		servsock.listen(40)

		servpoll.register(servsock, pollin | pollpri | pollhup | pollerr)

		while True:
			try:
				events = servpoll.poll()
				for fd,flags in events:
					mappedfd = servfdmap[fd]

					if flags & pollin or flags & pollpri:
						if mappedfd is servsock:
							connection, client_address = mappedfd.accept()
							fileno = connection.fileno()
							servfdmap[fileno] = connection
							servpoll.register(connection, pollin | pollpri | pollhup | pollerr)

							clients[fileno] = reqObj(connection)
							clients[fileno].init()

						else:
							try:
								if not clients[fd].receive():
									terminate(fd)
							except socket.error:
								terminate(fd)
					elif flags & pollhup or flags & pollerr:
						if mappedfd is servsock:
							raise RuntimeError("Server socket broken")
						else:
							terminate(fd)
			except select.error:
				pass