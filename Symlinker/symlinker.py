import os
import sys
import string
import tkinter
import time
import traceback

time.clock()

LINKTYPES_L = ['Symbolic file', 'Hardlink file', 'Symbolic dir', 'Junction dir']
LINKTYPES = {'Symbolic file': '',
             'Hardlink file': '/H',
             'Symbolic dir': '/D',
             'Junction dir': '/J'
            }
LINKTYPES_DIR = ['Symbolic dir', 'Junction dir', LINKTYPES['Symbolic dir'], LINKTYPES['Junction dir']]
LINKTYPES_FILE = ['Symbolic file', 'Hardlink file', LINKTYPES['Symbolic file'], LINKTYPES['Hardlink file']]

TRACER_AUTOVERIFY_DELAY = 0.5

COLOR_BLACK = '#000'
COLOR_YELLOW = '#aa0'
COLOR_GREEN = '#0a0'
COLOR_RED = '#a00'

def assert_linktypes(linktype, symbolpath, actualpath):
    if os.path.isdir(actualpath) and linktype not in LINKTYPES_DIR or \
    os.path.isfile(actualpath) and linktype not in LINKTYPES_FILE:
        message = 'Invalid linktype {linktype} for target path {target}'
        message = message.format(linktype=repr(linktype), target=repr(actualpath))
        raise TypeError(message)

def mklink(linktype, symbolpath, actualpath):
    symbolpath = os.path.abspath(symbolpath)
    actualpath = os.path.abspath(actualpath)
    try:
        assert_linktypes(linktype, symbolpath, actualpath)
    except TypeError:
        traceback.print_exc()
        return False
    command = 'mklink {linktype} "{symbolpath}" "{actualpath}"'
    command = command.format(linktype=linktype,
                             symbolpath=symbolpath,
                             actualpath=actualpath)
    print(''.join(c for c in command if c in string.printable))
    status_code = os.system(command)
    if status_code != 0:
        return False
    if linktype in LINKTYPES_DIR:
        symtype = 'symlink' if linktype == '/D' else 'junction'
        symlink_info = symtype + time.strftime('_%Y%m%d-%H%M%S.txt')
        symlink_info = os.path.join(actualpath, symlink_info)
        symlink_info = open(symlink_info, 'w')
        symlink_info.write('actual: ' + actualpath)
        symlink_info.write('\n')
        symlink_info.write(symtype + ': ' + symbolpath)
        symlink_info.close()


class LinkGUI:
    def __init__(self):
        self.t = tkinter.Tk()

        self.tracer_nextautoverify = 0
        self.tracer_lastkeystroke_verified = False
        self.tracer_activewaiter = False

        self.stringvar_actualpath = tkinter.StringVar()
        self.stringvar_dropdown = tkinter.StringVar()
        self.label_actualpath = tkinter.Label(self.t, text='Actual path:')
        self.label_symbolpath = tkinter.Label(self.t, text='Symbol path:')
        self.entry_actualpath = tkinter.Entry(self.t, width=70, textvariable=self.stringvar_actualpath)
        self.entry_symbolpath = tkinter.Entry(self.t, width=70)
        self.dropdown_linktype = tkinter.OptionMenu(self.t, self.stringvar_dropdown, *LINKTYPES_L)
        self.dropdown_linktype.configure(width=15)
        self.button_do_it = tkinter.Button(self.t, text='Do it.', command=self.do_it)

        self.stringvar_actualpath.trace('w', self.tracewatcher)
        self.stringvar_dropdown.trace('w', lambda *bb: self.tracer_verify_colors(False))
        self.stringvar_actualpath.set(os.getcwd())
        self.entry_symbolpath.insert(0, os.getcwd())

        self.label_actualpath.grid(row=0, column=0, sticky='e')
        self.label_symbolpath.grid(row=1, column=0, sticky='e')
        self.entry_actualpath.grid(row=0, column=1, sticky='ew')
        self.entry_symbolpath.grid(row=1, column=1, sticky='ew')
        self.dropdown_linktype.grid(row=2, column=0)
        self.button_do_it.grid(row=2, column=1, sticky='e')

        self.t.grid_columnconfigure(1, weight=1)
        self.t.mainloop()

    def do_it(self, *bb):
        linktype = self.stringvar_dropdown.get()
        linktype = LINKTYPES[linktype]
        actualpath = self.entry_actualpath.get()
        symbolpath = self.entry_symbolpath.get()
        status = mklink(linktype, actualpath=actualpath, symbolpath=symbolpath)
        if status is False:
            self.button_do_it.configure(bg=COLOR_RED)
        else:
            self.button_do_it.configure(bg=COLOR_GREEN)

    def tracewatcher(self, *bb):
        self.tracer_lastkeystroke_verified = False
        self.tracer_nextautoverify = time.time() + TRACER_AUTOVERIFY_DELAY
        if self.tracer_activewaiter is False:
            self.tracer_verify()

    def tracer_verify(self):
        now = time.time()
        if self.tracer_lastkeystroke_verified is True:
            return
        if now < self.tracer_nextautoverify:
            delay = int(TRACER_AUTOVERIFY_DELAY * 1000)
            self.t.after(delay, self.tracer_verify)
            self.tracer_activewaiter = True
            self.dropdown_linktype.config(fg=COLOR_YELLOW)
            return
        self.tracer_lastkeystroke_verified = True
        self.tracer_activewaiter = False

        self.tracer_verify_colors(set_for_me=True)

    def tracer_verify_colors(self, set_for_me=False, *bb):
        path = self.stringvar_actualpath.get()
        linktype = self.stringvar_dropdown.get()
        if os.path.isfile(path):
            if set_for_me and linktype not in LINKTYPES_FILE:
                self.stringvar_dropdown.set('Symbolic file')
                return
            if linktype in LINKTYPES_FILE:
                self.dropdown_linktype.config(fg=COLOR_GREEN)
            else:
                self.dropdown_linktype.config(fg=COLOR_BLACK)
        elif os.path.isdir(path):
            if set_for_me and linktype not in LINKTYPES_DIR:
                self.stringvar_dropdown.set('Symbolic dir')
                return
            if linktype in LINKTYPES_DIR:
                self.dropdown_linktype.config(fg=COLOR_GREEN)
            else:
                self.dropdown_linktype.config(fg=COLOR_BLACK)
        else:
            self.dropdown_linktype.config(fg=COLOR_BLACK)

#mklink(LINKTYPE_SYMBOLIC_DIR, 'examples\\symbolic_dir', 'examples\\actual_dir')
#mklink(LINKTYPE_JUNCTION_DIR, 'examples\\junction_dir', 'examples\\actual_dir')
#mklink(LINKTYPE_SYMBOLIC_FILE, 'examples\\symbolic_file.txt', 'examples\\actual_file.txt')
#mklink(LINKTYPE_HARDLINK_FILE, 'examples\\hardlink_file.txt', 'examples\\actual_file.txt')
linker = LinkGUI()
print('[ {0} elapsed ]'.format(round(time.clock(), 3)))

