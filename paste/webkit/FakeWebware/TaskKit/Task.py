from MiscUtils import AbstractError


class Task:

	def __init__(self):
		""" Subclasses should invoke super for this method. """
		# Nothing for now, but we might do something in the future.
		pass

	def run(self):
		"""
		Override this method for you own tasks. Long running tasks can periodically 
		use the proceed() method to check if a task should stop. 
		"""
		raise AbstractError, self.__class__
	
		
	## Utility method ##	
	
	def proceed(self):
		"""
		Should this task continue running?
		Should be called periodically by long tasks to check if the system wants them to exit.
		Returns 1 if its OK to continue, 0 if its time to quit
		"""
		return self._handle._isRunning
		
		
	## Attributes ##
	
	def handle(self):
		"""
		A task is scheduled by wrapping a handler around it. It knows
		everything about the scheduling (periodicity and the like).
		Under normal circumstances you should not need the handler,
		but if you want to write period modifying run() methods, 
		it is useful to have access to the handler. Use it with care.
		"""
		return self._handle

	def name(self):
		"""
		Returns the unique name under which the task was scheduled.
		"""
		return self._name


	## Private method ##

	def _run(self, handle):
		"""
		This is the actual run method for the Task thread. It is a private method which
		should not be overriden.
		"""
		self._name = handle.name()
		self._handle = handle
		self.run()
		handle.notifyCompletion()
