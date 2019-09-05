class Menu:
	""" Class which returns a menu object.

	Creates menu object which is to be displayed in the text based
	Commander1 module interface.

	Attributes:
		menues: Dictionary containing all created menu objects.
		name: Menu name, e.g. 'Main Menu'.
		items: List of items in the menu. Items must be strings.
		parent: If the menu is a submenu, i.e. the menu is entered from
			a previous menu during menu navigation, parent is the
			previous menu object.
		numbered: Activates numbering of items during display.
		format_menu_name: Menu name formated to be displayed as
			location info.
	Methods:
		set_instr(instr): Takes in a list of instructions or commands
			and makes it a menu property. The instructions are ment to
			display user key options during menu display.
	"""
	menues = {}


	def __init__(self, name, items, instructions, parent=None, info=None):
		"""
		Args:
			name: Menu name, e.g. 'Main Menu'.
			items: List of items in the menu. Items must be strings.
			parent: Previous menu object in menu hierarchy.
				Defaults to None.
		"""
		self.name = name
		self.items = items
		self.instructions = instructions
		self.parent = parent
		self.info = info
		self.numbered = True

		if self.name not in self.menues:
			self.menues.update({self.name:self})

	@property
	def format_menu_name(self):
		"""Returns formated version of menu name"""
		max_x_len = 37
		num_ = (max_x_len - len(self.name) - 2)//2
		name = self.name.strip('*')
		if len(self.name) % 2 == 0:
			return num_*'_' + f' {name} ' + num_*'_'+'_'
		else:
			return num_*'_' + f' {name} ' + num_*'_'

	def __str__(self):
		"""Renames menu object"""
		return f'Menu: {self.name}'


if __name__ == '__main__':
	help(Menu)
