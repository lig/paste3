import os, sys
sys.path.insert(1, os.path.abspath('../..'))
import TaskKit
#from MiscUtils import unittest
import unittest


class TaskKitTest(unittest.TestCase):

	def setUp(self):
		from TaskKit.Scheduler import Scheduler
		self.scheduler = Scheduler()

	def checkBasics(self):
		sched = self.scheduler
		sched.start()

	def tearDown(self):
		self.scheduler.stop()
		self.scheduler = None


def makeTestSuite():
	suite1 = unittest.makeSuite(TaskKitTest, 'check')
	return unittest.TestSuite((suite1,))


if __name__=='__main__':
	runner = unittest.TextTestRunner(stream=sys.stdout)
	unittest.main(defaultTest='makeTestSuite', testRunner=runner)
