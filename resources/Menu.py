class Menu:
	""" Class which returns a menu object.

	Creates menu object which is to be displayed in the text based
	Commander1 module interface.
	"""

	menues = {}
	def __init__(self, name, items, instructions, parent=None, info=None):
		self.name = name
		self.items = items
		self.instructions = instructions
		self.parent = parent
		self.info = info
		self.numbered = True

		if self.name not in self.menues:
			self.menues.update({self.name:self})

	def __str__(self):
		"""Renames menu object"""
		return f'Menu: {self.name}'

if __name__ == '__main__':
	help(Menu)
