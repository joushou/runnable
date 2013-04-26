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
	def __init__(self, port, reqObj):
		self.port = port
		self.reqObj = reqObj
		super(RunnableServer, self).__init__()

	def execute(self):
		if not issubclass(self.reqObj, RequestObject):
			raise RunnableServerError('reqObj not subclass of RequestObject')

		servsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		servsock.setblocking(0)
		servsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		servsock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
		servsock.settimeout(None)

		servfdmap = {servsock.fileno(): servsock}
		clients = {}

		try:
			servpoll = select.epoll()
			pollin, pollpri, pollhup, pollerr = select.EPOLLIN, select.EPOLLPRI, select.EPOLLHUP, select.EPOLLERR
		except AttributeError:
			servpoll = select.poll()
			pollin, pollpri, pollhup, pollerr = select.POLLIN, select.POLLPRI, select.POLLHUP, select.POLLERR

		def terminate(fd):
			try:
				servpoll.unregister(servfdmap[fd])
				clients[fd].destroy()
				del clients[fd]
				del servfdmap[fd]
			except socket.error:
				pass

		servsock.bind(("0.0.0.0", self.port))
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

							clients[fileno] = self.reqObj(connection)
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
