import math
import random
import shutil
import string
import threading
import time
import tkinter

# Nice patterns
# 0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345
# 0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330
# 0, 15, 30, 45, 60, 180, 195, 210, 225, 240
# 0, 90, 180, 270
# ░▒▓

SCREEN_WIDTH = shutil.get_terminal_size()[0] - 6
print(SCREEN_WIDTH)

DEFAULT_LINE = {
    'character': '#',
    'degree': 0,
    'degree_step': 1,
    'horizontal_offset': 0,
    'line_thickness': 1,
    'original_degree': 0,
    'damping': 3,
    'depth': 0,
}
variables = {
    'clock': 0,
    'frames':[],
    'delay': 0.02,
    'lines':[
    ]
}

class LineControl(tkinter.Frame):
    def __init__(self, master, line, *args, **kwargs):
        tkinter.Frame.__init__(self, master, *args, **kwargs)

        self.line = line
        for x in range(4):
            self.columnconfigure(x, minsize=40)
        row = 0
        tkinter.Button(self, text='\u21bb', command=self.refresh).grid(row=row, column=0, sticky='news')
        tkinter.Button(self, text='Clone', command=self.clone).grid(row=row, column=1, columnspan=2, sticky='news')
        tkinter.Button(self, text='X', command=self.suicide).grid(row=row, column=3, sticky='news')
        row += 1

        tkinter.Label(self, text='Degree:').grid(row=row, column=0, sticky='e')
        self.entry_degree = tkinter.Entry(self, width=3)
        self.entry_degree.insert(0, self.line['original_degree'])
        self.entry_degree.grid(row=row, column=1, sticky='news')
        tkinter.Button(self, text='Set', command=self.apply_degree).grid(row=row, column=2, sticky='news')
        row += 1

        def create_buttonpair(key, row):
            minus = tkinter.Button(self, text='-', command=lambda *a: self.step_variable(key, -1, self.value_labels[key]))
            minus.grid(row=row, column=1, sticky='news')
            plus = tkinter.Button(self, text='+', command=lambda *a: self.step_variable(key, +1, self.value_labels[key]))
            plus.grid(row=row, column=2, sticky='news')

        self.value_labels = {}
        tkinter.Label(self, text='Step:').grid(row=row, column=0, sticky='e')
        create_buttonpair('degree_step', row)
        self.value_labels['degree_step'] = tkinter.Label(self, text=str(self.line['degree_step']))
        self.value_labels['degree_step'].grid(row=row, column=3)
        row += 1

        tkinter.Label(self, text='Thick:').grid(row=row, column=0, sticky='e')
        create_buttonpair('line_thickness', row)
        self.value_labels['line_thickness'] = tkinter.Label(self, text=str(self.line['line_thickness']))
        self.value_labels['line_thickness'].grid(row=row, column=3)
        row += 1

        tkinter.Label(self, text='Offset:').grid(row=row, column=0, sticky='e')
        create_buttonpair('horizontal_offset', row)
        self.value_labels['horizontal_offset'] = tkinter.Label(self, text=str(self.line['horizontal_offset']))
        self.value_labels['horizontal_offset'].grid(row=row, column=3)
        row += 1

        tkinter.Label(self, text='Dampen:').grid(row=row, column=0, sticky='e')
        create_buttonpair('damping', row)
        self.value_labels['damping'] = tkinter.Label(self, text=str(self.line['damping']))
        self.value_labels['damping'].grid(row=row, column=3)
        row += 1

        tkinter.Label(self, text='Depth:').grid(row=row, column=0, sticky='e')
        create_buttonpair('depth', row)
        self.value_labels['depth'] = tkinter.Label(self, text=str(self.line['depth']))
        self.value_labels['depth'].grid(row=row, column=3)
        row += 1

        tkinter.Label(self, text='Char:').grid(row=row, column=0, sticky='e')
        self.entry_character = tkinter.Entry(self, width=2, font=('Consolas', 12))
        self.entry_character.grid(row=row, column=1, sticky='news')
        self.entry_character.insert(0, self.line['character'])
        tkinter.Button(self, text='Set', command=self.apply_character).grid(row=row, column=2, sticky='news')
        row += 1

    def apply_character(self, *trash):
        char = self.entry_character.get()
        try:
            assert len(char) == 1
        except:
            return
        self.line['character'] = char

    def apply_degree(self, *trash):
        value = self.entry_degree.get()
        try:
            value = int(value)
        except ValueError:
            return
        self.line['original_degree'] = value % 360
        self.refresh()
        regrid_frames()

    def clone(self, *trash):
        line = self.line.copy()
        create_line_frame(line=line)
        regrid_frames()

    def refresh(self, *trash):
        self.line['degree'] = self.line['original_degree'] + (self.line['degree_step'] * variables['clock'])

    def step_variable(self, key, direction, label):
        value = self.line[key]
        value += direction

        if key == 'line_thickness':
            value = max(value, 0)
        elif key == 'horizontal_offset':
            value = value % SCREEN_WIDTH
        elif key == 'delay':
            value = max(value, 0.001)
        elif key in ('damping', 'depth'):
            value = max(value, 0)
            value = min(value, int(SCREEN_WIDTH / 2))

        self.line[key] = value
        label.configure(text=str(value)[:5])

    def suicide(self, *trash):
        unregister_line(self.line)
        variables['frames'].remove(self)
        self.grid_forget()
        regrid_frames()

def create_line(degree_offset, **kwargs):
    line = DEFAULT_LINE.copy()
    line.update(kwargs)
    line['original_degree'] = degree_offset
    line['degree'] = (variables['clock'] + degree_offset) % 360
    # Line ID exists solely to make sure that even clones are unique.
    line['id'] = random.getrandbits(32)
    return line

def create_line_frame(offset=None, line=None):
    if line is None:
        if offset is None:
            offset = t.entry_add.get()
            offset = offset.replace(' ', '')
            offset = offset.split(',')
            try:
                offset = [int(o) for o in offset]
            except ValueError:
                return
            t.entry_add.delete(0, 'end')

        lines = []
        for x in offset:
            line = create_line(x)
            lines.append(line)
    else:
        line['id'] = random.getrandbits(32)
        lines = [line]

    for line in lines:
        register_line(line)
        frame = LineControl(t, line, relief='groove', borderwidth=2)
        variables['frames'].append(frame)
    regrid_frames()

def map_range(x, old_low, old_high, new_low, new_high):
    '''
    Given a number x in range [old_low, old_high], return corresponding
    number in range [new_low, new_high].
    '''
    if x > old_high or x < old_low:
        raise ValueError('%d not in range [%d..%d]' % (x, old_low, old_high))
    percentage = (x - old_low) / (old_high - old_low)
    y = (percentage * (new_high - new_low)) + new_low
    return y

def position_from_degree(d, damping_units):
    rad = math.radians(d)
    sin = math.sin(rad)
    sin = map_range(sin, -1, 1, 0, 1)
    position = sin * (SCREEN_WIDTH - 1)
    position = map_range(position, 0, SCREEN_WIDTH, damping_units, SCREEN_WIDTH-damping_units)
    #position = (position * (1- (2 * damping_percent))) + damping_units
    position = round(position)
    position = position % SCREEN_WIDTH
    return position

def print_loop():
    while True:
        next_frame = time.time() + variables['delay']
        variables['clock'] = (variables['clock'] + 1) % 360

        screen = ([' '] * SCREEN_WIDTH)
        z_indexes = {}

        for line_vars in variables['lines']:
            start_degree = line_vars['degree']
            end_degree = (start_degree + line_vars['degree_step']) % 360
            line_vars['degree'] = end_degree

            damping = line_vars['damping']
            start_pos = position_from_degree(start_degree, damping)
            end_pos = position_from_degree(end_degree, damping)
            (start_pos, end_pos) = sorted([start_pos, end_pos])

            start_pos -= line_vars['line_thickness']
            end_pos += line_vars['line_thickness']

            mini_step = line_vars['degree_step'] / max((end_pos - start_pos), 1)
            for (index, position) in enumerate(range(start_pos, end_pos+1)):
                position = (position + line_vars['horizontal_offset']) % SCREEN_WIDTH
                this_rads = math.radians(start_degree + (mini_step * index))
                z_index = math.cos(this_rads)
                z_index = map_range(z_index, -1, 1, line_vars['depth'], SCREEN_WIDTH-line_vars['depth'])
                #print(line_vars['character'], z_index)
                if z_index > z_indexes.get(position, -2):
                    screen[position] = line_vars['character']
                    z_indexes[position] = z_index

        print('%03d' % variables['clock'], ''.join(screen))
        delay = max(next_frame - time.time(), 0)
        time.sleep(delay)

def register_line(line):
    variables['lines'].append(line)

def regrid_frames():
    frames = variables['frames']
    #frames.sort(key=lambda x: x.line['original_degree'])
    for (index, frame) in enumerate(frames):
        (row, column) = divmod(index, 4)
        row += 1
        frame.grid(row=row, column=column)

def unregister_line(line):
    variables['lines'].remove(line)

def main():
    global t
    t = tkinter.Tk()

    frame_add = tkinter.Frame(t)
    entry_add = tkinter.Entry(frame_add)
    t.entry_add = entry_add
    entry_add.grid(row=0, column=0)
    tkinter.Button(frame_add, text='+', command=create_line_frame).grid(row=0, column=1)
    frame_add.grid(row=0, column=0)

    frame_delay = tkinter.Frame(t)
    tkinter.Label(frame_delay, text='Speed:')
    thread = threading.Thread(target=print_loop)
    thread.daemon=True
    thread.start()

    create_line_frame([0])
    t.mainloop()

if __name__ == '__main__':
    main()
