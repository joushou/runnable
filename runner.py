from __future__ import print_function, absolute_import, unicode_literals, division
from runnable.runnable import Runnable
from collections import deque

class RunnerError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

class Runner(object):
	def __init__(self):
		self._queue = deque()

	def queue(self, r):
		if not isinstance(r, Runnable):
			raise RunnerError('Object not Runnable')
		self._queue.append(r)

	def run(self):
		r = self._queue.popleft()
		print(r.execute())
