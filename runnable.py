from __future__ import print_function, absolute_import, unicode_literals, division
from copy_reg import pickle
from types import CodeType
from new import code, function

def code_ctor(argcount, nlocals, stacksize, flags, cocode,
              consts, names, varnames, filename, name,
              firstlineno, lnotab, freevars, cellvars):
	return code(argcount, nlocals, stacksize, flags, cocode,
	            consts, names, varnames, filename, name,
	            firstlineno, lnotab, freevars, cellvars)

def reduce_code(co):
	return code_ctor, (co.co_argcount, co.co_nlocals,
	                   co.co_stacksize, co.co_flags,
	                   co.co_code, co.co_consts,
	                   co.co_names, co.co_varnames,
	                   co.co_filename, co.co_name,
	                   co.co_firstlineno, co.co_lnotab,
	                   co.co_freevars, co.co_cellvars)
pickle(CodeType, reduce_code)

class Runnable(object):
	'''Runnable

Runnable objects are able to pickle the execute methods code-object,
meaning that it can be serialized and executed on another Python
instance, with the only requirement being having this module loaded.

Potentially very buggy.'''
	def __init__(self, properties=None):
		'Accepts a property for use by the Runnable.'
		self.properties = properties

	def __getstate__(self):
		return (self.execute.__func__.__code__,
		        self.properties)

	def __setstate__(self, m):
		self.execute.__func__.__code__ = m[0]
		self.properties = m[1]

	def __reduce__(self):
		return (Runnable, (), self.__getstate__())

	def __reduce_ex__(self, version):
		return self.__reduce__()

	def execute(self):
		'Execute; To be implemented by subclass.'
		return NotImplemented

class TargetRunnable(Runnable):
	'Like Runnable, but takes the target function as argument.'
	def __init__(self, target=None, arguments=None):
		'Takes a function as target, as well as arguments for the function.'
		super(TargetRunnable, self).__init__(properties=(target, arguments))

	def execute(self):
		'Execute the target.'
		f = function(*self.properties[0])
		return f(self.properties[1])

class ExecRunnable(Runnable):
	'Like Runnable, but takes the source as a string.'
	def __init__(self, source='', filename='', loc={}, glob={}):
		if type(source) == unicode or type(source) == str:
			source = compile(source, filename, mode='exec', dont_inherit=True)
		super(ExecRunnable, self).__init__(properties=(source, loc, glob))

	def execute(self):
		'Execute the compiled source'
		exec(self.properties[0], self.properties[1], self.properties[2])
		return self.properties[1], self.properties[2]
