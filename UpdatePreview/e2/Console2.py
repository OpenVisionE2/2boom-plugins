# -*- coding: utf-8 -*-
from enigma import eConsoleAppContainer
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel


class Console2(Screen):
	skin = """
		<screen position="center,140" size="1100,520" title="Upgrade execution..." >
			<widget name="text" position="10,10" size="1080,470" font="Console;22" />
		</screen>"""

	def __init__(self, session, title="Console", cmdlist=None, finishedCallback=None, closeOnSuccess=False):
		Screen.__init__(self, session)

		self.finishedCallback = finishedCallback
		self.closeOnSuccess = closeOnSuccess
		self.errorOcurred = False

		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"ok": self.cancel,
			"back": self.cancel,
			"up": self["text"].pageUp,
			"down": self["text"].pageDown
		}, -1)

		self.cmdlist = cmdlist
		self.newtitle = title

		self.onShown.append(self.updateTitle)

		self.container = eConsoleAppContainer()
		self.run = 0
		self.container.appClosed.append(self.runFinished)
		self.container.dataAvail.append(self.dataAvail)
		self.onLayoutFinish.append(self.startRun)

	def updateTitle(self):
		self.setTitle(self.newtitle)

	def startRun(self):
		self["text"].setText("")
		print("Console: executing in run", self.run, " the command:", self.cmdlist[self.run])
		if self.container.execute(self.cmdlist[self.run]):
			self.runFinished(-1) # so we must call runFinished manual

	def runFinished(self, retval):
		if retval:
			self.errorOcurred = True
		self.run += 1
		if self.run != len(self.cmdlist):
			if self.container.execute(self.cmdlist[self.run]): #start of container application failed...
				self.runFinished(-1) # so we must call runFinished manual
		else:
			lastpage = self["text"].isAtLastPage()
			str = self["text"].getText()
			str += _("Execution finished!!")
			self["text"].setText(str)
			self.setTitle(_("Execution finished!!"))
			if lastpage:
				self["text"].lastPage()
			if self.finishedCallback is not None:
				self.finishedCallback()
			if not self.errorOcurred and self.closeOnSuccess:
				self.cancel()

	def cancel(self):
		if self.run == len(self.cmdlist):
			self.close()
			self.container.appClosed.remove(self.runFinished)
			self.container.dataAvail.remove(self.dataAvail)

	def dataAvail(self, str):
		lastpage = self["text"].isAtLastPage()
		self["text"].setText(self["text"].getText() + str)
		if lastpage:
			self["text"].lastPage()
