import datetime
import shutil
import sqlite3
import sys
import textwrap

try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except:
    HAS_COLORAMA = False

SQL_ID = 0
SQL_TODOTABLE = 1
SQL_CREATED = 2
SQL_MESSAGE = 3

HELP_FULL = [
('> toddo', 'Display the todos from the current table'),
('> toddo all', 'Display the todos from all tables'),
('> toddo 4', 'Display the todo with ID 4'),
('> toddo add', 'Add a new todo via multi-line typing prompt'),
('> toddo add "message"', 'Add a new todo with this message'),
('> toddo remove 8', 'Remove the todo with ID 8'),
('> toddo table', 'Display the name of the current table'),
('> toddo table name', 'Switch to the table named "name"')
]

HELP_NOENTRIES = '''Your todo list is empty!
Use `toddo add` or `toddo add "message"` to make entries.'''

HELP_NOACTIVE = '''Table `%s` has no entries!
Use `toddo all` to see if there are entries for other tables.'''

HELP_REMOVE = '''Provide an ID number to remove.'''

# The newline at the top of this message is intentional
DISPLAY_INDIVIDUAL = '''
     ID: _id_
  Table: _table_
Created: _human_
Message: _message_'''

class ToddoExc(Exception):
    pass

class Toddo():
    def __init__(self, dbname='C:/git/else/toddo/toddo.db'):
        self.dbname = dbname
        self._sql = None
        self._cur = None

    @property
    def sql(self):
        if self._sql is None:
            self._sql = sqlite3.connect(self.dbname)
        return self._sql

    @property
    def cur(self):
        if self._cur is None:
            self._cur = self.sql.cursor()
            self._cur.execute('CREATE TABLE IF NOT EXISTS meta(key TEXT, val TEXT)')
            self._cur.execute('CREATE TABLE IF NOT EXISTS todos(id INT, todotable TEXT, created INT, message TEXT)')
            self._cur.execute('CREATE INDEX IF NOT EXISTS todoindex on todos(id)')
        return self._cur

    def _install_default_lastid(self):
        self.cur.execute('SELECT val FROM meta WHERE key == "lastid"')
        f = cur.fetchone()
        if f is not None:
            return int(f[0])
        self.cur.execute('INSERT INTO meta VALUES("lastid", 1)')
        self.sql.commit()
        return 1

    def _install_default_todotable(self):
        self.cur.execute('SELECT val FROM meta WHERE key == "todotable"')
        f = cur.fetchone()
        if f is not None:
            return f[0]
        self.cur.execute('INSERT INTO meta VALUES("todotable", "default")')
        self.sql.commit()
        return 'default'

    def add_todo(self, message=None):
        '''
        Create new entry in the database on the active todotable.
        '''
        if message is None:
            message = multi_line_input()
        message = str(message)
        if message is '':
            raise ToddoExc('Todos cannot be blank.')

        todoid = self.increment_lastid()
        todotable = self.get_todotable()
        created = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        self.cur.execute('INSERT INTO todos VALUES(?, ?, ?, ?)', [todoid, todotable, created, message])
        self.sql.commit()
        return todoid
    
    def remove_todo(self, idnumber):
        '''
        Drop todo from the database.
        '''
        idnumber = int(idnumber)
        self.cur.execute('SELECT * FROM todos WHERE id=?', [idnumber])
        todo = self.cur.fetchone()
        if todo is None:
            raise ToddoExc('Todo %d does not exist.' % idnumber)
        activetable = self.get_todotable()
        requestedtable = todo[SQL_TODOTABLE]
        if requestedtable.lower() != activetable.lower():
            raise ToddoExc('Todo %d is not part of the active table `%s`. It belongs to `%s`.' % (idnumber, activetable, requestedtable))
        print(self.display_one_todo(idnumber))
        self.cur.execute('DELETE FROM todos WHERE id=?', [idnumber])
        self.sql.commit()
        return idnumber

    def display_one_todo(self, idnumber):
        '''
        Make a nice display that shows a todo's entire contents.
        '''
        self.cur.execute('SELECT * FROM todos WHERE id=?', [idnumber])
        todo = self.cur.fetchone()
        if todo is None:
            raise ToddoExc('Todo %d does not exist.' % idnumber)
        
        message = todo[SQL_MESSAGE]
        messageleft = len('Message: ')
        width = shutil.get_terminal_size()[0] - (messageleft + 1)
        message = nicewrap(message, width, messageleft)

        output = DISPLAY_INDIVIDUAL
        output = output.replace('_id_', str(todo[SQL_ID]))
        output = output.replace('_table_', todo[SQL_TODOTABLE])
        output = output.replace('_human_', human(todo[SQL_CREATED]))
        output = output.replace('_message_', message)

        return output

    def display_active_todos(self):
        '''
        Pass the active table name into display_todos_from_table
        '''
        todotable = self.get_todotable()
        return self.display_todos_from_table(todotable)
        
    def display_todos_from_table(self, todotable):
        '''
        Make a nice display from the database.
        '''
        if todotable is None:
            self.cur.execute('SELECT * FROM todos ORDER BY id ASC')
        else:
            self.cur.execute('SELECT * FROM todos WHERE todotable=? ORDER BY id ASC', [todotable])
        todos = self.cur.fetchall()
        if len(todos) == 0:
            return None

        todos = [list(x) for x in todos]

        longest_id = max(len(str(x[SQL_ID])) for x in todos)
        longest_table = max(len(str(x[SQL_TODOTABLE])) for x in todos)

        display = []
        for todo in todos:
            todoid = str(todo[SQL_ID])
            todoid = (' '*(longest_id-len(todoid))) + todoid

            timestamp = human(todo[SQL_CREATED])

            todotable = todo[SQL_TODOTABLE]
            todotable = (' '*(longest_table-len(todotable))) + todotable

            message = todo[SQL_MESSAGE]
            if '\n' in message:
                message = message.split('\n')[0] + ' ...'

            terminal_width = shutil.get_terminal_size()[0]
            total = '%s : %s : %s' % (timestamp, todoid, message)
            space_remaining = terminal_width - len(total)
            if len(total) > terminal_width:
                total = total[:(terminal_width-(len(total)+4))] + '...'
            display.append(total)

        return '\n'.join(display)

    def get_todotable(self):
        self.cur.execute('SELECT val FROM meta WHERE key="todotable"')
        todotable = self.cur.fetchone()
        if todotable is None:
            self._install_default_todotable()
            todotable = 'default'
        else:
            todotable = todotable[0]
        return todotable

    def increment_lastid(self, increment=False):
        '''
        Increment the lastid in the meta table, THEN return it.
        '''
        self.cur.execute('SELECT val FROM meta WHERE key="lastid"')
        lastid = self.cur.fetchone()
        if lastid is None:
            self._install_default_lastid()
            return 1
        else:
            lastid = int(lastid[0]) + 1
            self.cur.execute('UPDATE meta SET val=? WHERE key="lastid"', [lastid])
            return lastid
    
    def switch_todotable(self, newtable=None):
        '''
        Update the meta with `newtable` as the new active todotable.
        '''
        self.cur.execute('SELECT val FROM meta WHERE key="todotable"')
        activetable = self.cur.fetchone()
        if not activetable:
            activetable = self._install_default_todotable()
        else:
            activetable = activetable[0]
        if newtable is None:
            return activetable
        self.cur.execute('UPDATE meta SET val=? WHERE key="todotable"', [newtable])
        self.sql.commit()
        return newtable

def colorama_print(text):
    alternator = False
    terminal_size = shutil.get_terminal_size()[0]
    for line in text.split('\n'):
        line += ' ' * (terminal_size - (len(line)+1))
        if HAS_COLORAMA:
            if alternator:
                sys.stdout.write(colorama.Fore.BLACK)
                sys.stdout.write(colorama.Back.WHITE)
            else:
                sys.stdout.write(colorama.Fore.WHITE)
                sys.stdout.write(colorama.Back.BLACK)
        alternator = not alternator
        print(line)
    if HAS_COLORAMA:
        sys.stdout.write(colorama.Back.RESET)
        sys.stdout.write(colorama.Fore.RESET)
        sys.stdout.flush()

def human(timestamp):
    timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    timestamp = datetime.datetime.strftime(timestamp, '%d %b %Y %H:%M')
    return timestamp

def multi_line_input():
    print('Submit a ctrl+z to finish typing.')
    userinput = ''
    ctrlz = '\x1a'
    while True:
        try:
            additional = input('- ')
        except EOFError:
            # If you only enter a ctrlz
            return userinput

        if ctrlz in additional:
            additional = additional.split(ctrlz)[0]
            userinput += additional
            break

        userinput += additional + '\n'

    return userinput.strip()

def nicewrap(message, width, paddingleft):
    # http://stackoverflow.com/a/26538082 ##########################
    message = '\n'.join(['\n'.join(textwrap.wrap(line, width,#######
         break_long_words=True, replace_whitespace=False))##########
         for line in message.split('\n')])##########################
    ################################################################
    message = message.strip()
    message = message.replace('\n', '\n' + (' '*paddingleft))
    return message

def fullhelp():
    longestleft = max(len(x[0]) for x in HELP_FULL)
    width = shutil.get_terminal_size()[0] - 1
    message = []
    for item in HELP_FULL:
        pad = width - (longestleft+ 3)
        item = '%s : %s' % (item[0] + (' '*(longestleft - len(item[0]))), nicewrap(item[1], pad, longestleft + 3))
        message.append(item)
    message = '\n'.join(message)
    return message


if __name__ == '__main__':
    toddo = Toddo()

    # Look, no more IndexErrors
    sys.argv += [None]*10

    if isinstance(sys.argv[1], str):
        sys.argv[1] = sys.argv[1].lower()

    if sys.argv[1] is None:
        message = toddo.display_active_todos()
        if message is None:
            table = toddo.get_todotable()
            print(HELP_NOACTIVE % table)
        else:
            colorama_print(message)

    elif sys.argv[1] == 'all':
        message = toddo.display_todos_from_table(None)
        if message is None:
            print(HELP_NOENTRIES)
        else:
            colorama_print(message)

    elif sys.argv[1] == 'add':
        args = list(filter(None, sys.argv))
        args = args[2:]
        args = ' '.join(args)
        if args == '':
            args = None
        message = toddo.add_todo(args)
        if isinstance(message, int):
            print('Added %d' % message)

    elif sys.argv[1] == 'remove':
        idnumber = sys.argv[2]
        if idnumber is None or not idnumber.replace(',', '').isdigit():
            print(HELP_REMOVE)
        else:
            message = []
            ids = [int(x) for x in idnumber.split(',')]
            for x in ids:
                try:
                    t = toddo.remove_todo(x)
                    message.append('Removed %d' % t)
                except ToddoExc as e:
                    message.append(e.args[0])
            print('\n'.join(message))

    elif sys.argv[1] == 'table':
        currenttable = toddo.get_todotable()
        message = toddo.switch_todotable(sys.argv[2])
        if currenttable == message:
            print('You are on table `%s`' % message)
        else:
            print('Switched to table `%s`' % message)

    elif sys.argv[1].isdigit():
        try:
            message = toddo.display_one_todo(int(sys.argv[1]))
            print(message)
        except ToddoExc as e:
            print(e.args[0])

    elif sys.argv[1] == 'help':
        print(fullhelp())

    else:
        print('Command not recognized.')
        print(fullhelp())
