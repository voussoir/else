import copy
class StackError(Exception):
	pass


class Stack:
	"""
	Class to replicate a Stack data structure.
	Attributes: maxlen, name
	Methods: pop, populate, push, top, truncate
	"""
	def __init__(self, maxlen=None, name=""):
		self.maxlen = maxlen
		self.name = str(name)
		self.data = []

	def __get__(self):
		return self.data

	def __len__(self):
		return len(self.data)

	def __getitem__(self, index):
		return self.data[index]

	def __setattr__(self, key, value):
		if key == "name":
			value = str(value)
		if key == "maxlen" and value is not None:
			if value < 0:
				raise StackError()
			if len(self) > value:
				sizediff = len(self) - value
				sizediff = str(sizediff)
				e = ("Cannot set `maxlen` below current `len` or %s items "
				"would be lost. Try Stack.pop(%s) or Stack.truncate(%d)")
				raise StackError(e % (sizediff, sizediff, value))
		if key == "data" and self.maxlen is not None:
			if len(value) > self.maxlen:
				raise StackError("List is longer than `maxlen` (%d/%d)" %
					(len(value), self.maxlen))
		super(Stack, self).__setattr__(key, value)

	def __repr__(self):
		display = self.name
		display += "[|"
		display += ', '.join([item.__repr__() for item in self.data])
		display += "|]"
		if self.maxlen is not None:
			display += str(self.maxlen - len(self))
		return display

	def deepcopy(self):
		"""
		Return a deep copy of this Stack as a new object
		"""
		copystack = Stack(self.maxlen, self.name)
		copystack.populate(copy.deepcopy(self.data))
		return copystack

	def pop(self, count=1):
		"""
		Pop the last `count` items off of the Stack. Default 1
		returns the most recently popped item
		"""
		for c in range(count):
			if len(self) == 0:
				raise StackError("Cannot pop from empty Stack")
			lastitem = self.data[-1]
			self.data = self.data[:-1]
		return lastitem

	def populate(self, itemlist, destructive=False):
		"""
		Push as many items as possible from `itemlist` onto the Stack
		if `destructive`==True, the current data will be overwritten
		and discard the rest.
		"""
		if isinstance(itemlist, range):
			itemlist = list(itemlist)
		if isinstance(itemlist, list):
			if destructive:
				itemlist = itemlist[:self.maxlen]
				self.data = itemlist
			else:
				if self.maxlen:
					itemlist = itemlist[:self.maxlen - len(self)]
				self.data += itemlist
		else:
			raise StackError("Stack.populate only accepts list or range type")

	def push(self, item):
		"""
		Push an item onto the end of the Stack
		"""
		if item is self:
			raise StackError("Cannot push Stack onto itself")
		if self.maxlen is None or len(self) < self.maxlen:
			self.data.append(item)
		else:
			raise StackError("Cannot push item onto full Stack")

	def top(self):
		"""
		Return the item on the top of the stack without popping it
		"""
		if len(self) > 0:
			return self.data[-1]
		else:
			raise StackError("Stack is empty")

	def truncate(self, value):
		"""
		Remove all items from the Stack after index `value`, and set
		`maxlen` to `value`, preventing the addition of further items.
		returns None
		"""
		self.data = self.data[:value]
		self.maxlen = value