Stack
======

A class to imitate the [Stack](http://en.wikipedia.org/wiki/Stack_(abstract_data_type)) data structure.


    class Stack:
    	Class to replicate a Stack data structure.
    	Attributes: maxlen, name
    	Methods: copy, pop, populate, push, top, truncate
    
    	def copy(self):
    		Return a deep copy of this Stack as a new object
    
    	def pop(self, count=1):
    		Pop the last `count` items off of the Stack. Default 1
    		returns the most recently popped item
    
    	def populate(self, itemlist, destructive=False):
    		Push as many items as possible from `itemlist` onto the Stack
    		and discard the rest.
    		if `destructive` is True, the current data will be overwritten
    
    	def push(self, item):
    		Push an item onto the top of the Stack
    
    	def top(self):
    		Return the item on the top of the stack without popping it
    
    	def truncate(self, value):
    		Remove all items from the Stack after index `value`, and set
    		`maxlen` to `value`, preventing the addition of further items.
    		returns None
    