import os

class ExistingChild(Exception):
    pass

class InvalidIdentifier(Exception):
    pass

class Tree:
    def __init__(self, identifier, data=None):
        if not isinstance(identifier, str):
            print(identifier)
            raise InvalidIdentifier('Identifiers must be strings')

        identifier = identifier.replace('/', os.sep)
        identifier = identifier.replace('\\', os.sep)
        if os.sep in identifier:
            raise InvalidIdentifier('Identifier cannot contain slashes')

        self.identifier = identifier
        self.data = data
        self.parent = None
        self.children = {}

    def __eq__(self, other):
        return isinstance(other, Tree) and self.abspath() == other.abspath()

    def __getitem__(self, key):
        return self.children[key]

    def __hash__(self):
        return hash(self.abspath())

    def __repr__(self):
        return 'Tree(%s)' % self.identifier

    def abspath(self):
        node = self
        nodes = [node]
        while node.parent is not None:
            node = node.parent
            nodes.append(node)
        nodes.reverse()
        nodes = [node.identifier for node in nodes]
        return '\\'.join(nodes)

    def add_child(self, other_node, overwrite_parent=False):
        self.check_child_availability(other_node.identifier)
        if other_node.parent is not None and not overwrite_parent:
            raise ValueError('That node already has a parent. Try `overwrite_parent=True`')

        other_node.parent = self
        self.children[other_node.identifier] = other_node
        return other_node

    def check_child_availability(self, identifier):
        if identifier in self.children:
            raise ExistingChild('Node %s already has child %s' % (self.identifier, identifier))

    def detach(self):
        if self.parent is None:
            return

        del self.parent.children[self.identifier]
        self.parent = None

    def list_children(self, customsort=None):
        children = list(self.children.values())
        if customsort is None:
            children.sort(key=lambda node: node.identifier.lower())
        else:
            children.sort(key=customsort)
        return children

    def merge_other(self, othertree, otherroot=None):
        newroot = None
        if ':' in othertree.identifier:
            if otherroot is None:
                raise Exception('Must specify a new name for the other tree\'s root')
            else:
                newroot = otherroot
        else:
            newroot = othertree.identifier
        othertree.identifier = newroot
        othertree.detach()
        othertree.parent = self
        self.check_child_availability(newroot)
        self.children[newroot] = othertree

    def walk(self, customsort=None):
        yield self
        for child in self.list_children(customsort=customsort):
            yield from child.walk(customsort=customsort)

    def walk_parents(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent
