import tkinter
import datetime
import math
import time

COLOR_BACKGROUND = '#000'
COLOR_FONT = '#666'
COLOR_DROPDOWN = '#aaa'
COLOR_DROPDOWN_ACTIVE = '#999'

MODE_CLOCK = 'clock'
MODE_COUNTDOWN = 'countdown'
MODE_STOPWATCH = 'stopwatch'

# Monospace fonts work best
FONT = 'Consolas'

# Used for resizing the clock font to fit the frame.
# For consolas, 1.33333 is a good value. It may differ
# for other fonts
FONT_YX_RATIO = 1.33333

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
MONTHS_DICT = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}

class Clock:
    def __init__(self):
        self.t = tkinter.Tk()
        self.t.configure(bg=COLOR_BACKGROUND)
        self.mode_methods = {
            MODE_CLOCK: self.build_gui_clock,
            MODE_COUNTDOWN: self.build_gui_countdown,
            MODE_STOPWATCH: self.build_gui_stopwatch,
        }
        self.dropstring = tkinter.StringVar(self.t)
        self.dropstring.trace('w', self.trigger_choose_mode)
        modes = list(self.mode_methods.keys())
        modes.sort(key=lambda x: x.lower())
        self.drop = tkinter.OptionMenu(self.t, self.dropstring, *modes)
        self.drop.configure(relief='flat', bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE, direction='below', highlightthickness=0, anchor='w')
        self.drop.pack(fill='x', anchor='n')
        #self.trigger_choose_mode()

        self.frame_applet = tkinter.Frame(self.t, width=400, height=95, bg=COLOR_BACKGROUND)
        self.frame_applet.pack(side='bottom', anchor='s', expand=True, fill='both')
        self.frame_applet.pack_propagate(0)
        self.frame_applet.grid_propagate(0)

        # tkinter elements belonging to any particular applet.
        # They will be destroyed when switching modes.
        # The dropdown and the frame_applet are not included here.
        self.elements = []

        # Instance is used to keep track of how many times we have
        # swapped modes.
        # This is to make sure that any `self.t.after` loops are broken
        # when we leave that mode.
        self.instance = 0
        
        self.dropstring.set(MODE_CLOCK)

        self.t.mainloop()

    @property
    def mode(self):
        return self.drop.cget('text')


    '''clock
     ######   ###        #####     ######   ### ###
    #######   ###       #######   #######   ### ###
    ###       ###       ### ###   ###       #####
    #######   #######   #######   #######   ### ###
     ######   #######    #####     ######   ### ###
    '''
    def build_gui_clock(self):
        '''
        A clock using the system's local time in 24 hour format.
        '''
        def tick_clock():
            if this_instance != self.instance:
                # used to break the "after" loop
                return
            #now = datetime.datetime.now()
            #now = now.strftime('%H:%M:%S')
            now = time.strftime('%H:%M:%S')
            label_clock.configure(text=now)
            self.t.after(1000, tick_clock)
        
        this_instance = self.instance

        label_clock = tkinter.Label(self.frame_applet, text='x', bg=COLOR_BACKGROUND, fg=COLOR_FONT)
        label_clock.pack(anchor='center', expand=True)
        self.elements.append(label_clock)

        tick_clock()
        self.frame_applet.bind('<Configure>', lambda event: self.resize_widget_font(self.frame_applet, label_clock))
        self.resize_widget_font(self.frame_applet, label_clock)


    '''countdown
     ######    #####    ### ###    #####    #######
    #######   #######   ### ###   #######   #######
    ###       ### ###   ### ###   ### ###     ###  
    #######   #######   #######   ### ###     ###  
     ######    #####     #####    ### ###     ###  
    '''
    def build_gui_countdown(self):
        '''
        A timer with two modes:
        1. "in" - countdown a certain amount of time. Ex "5 hours"
           This mode can be paused and resumed and the timer will pick up where it left off

        2. "until" - countdown until a certain moment. Ex "13 august 2015 15:00"
           In this mode, pausing only affects the display. Resuming the clock will skip to
           maintain the correct end time.
        '''
        def toggle_mode():
            reset_countdown()

            if label_countdown.mode is 'until':
                # "in" mode does not need the dd mmm yyyy boxes
                for item in elements_until:
                    item.grid_forget()
                # "in" mode can have arbitrary hours
                spinbox_hour.configure(to=999)
                label_countdown.mode = 'in'
            else:
                spinbox_day.grid(row=0, column=1)
                spinbox_month.grid(row=0, column=2)
                spinbox_year.grid(row=0, column=3)
                spinbox_hour.configure(to=23)
                label_countdown.mode = 'until'
            button_countdownmode.configure(text=label_countdown.mode)
        
        def tick_countdown():
            if this_instance != self.instance:
                return
            if not label_countdown.is_running:
                return
            
            now = time.time()
            if now > label_countdown.destination:
                reset_countdown()
                return

            until_dest = label_countdown.destination - now
            hours, minutes, seconds = self.hms_divmod(until_dest)
            display = '%02d:%02d:%04.1f' % (hours, minutes, seconds)
            display = display.replace('60.0', '00.0')
            previous_size = len(label_countdown.cget('text'))
            label_countdown.configure(text=display)
            if len(display) != previous_size:
                self.resize_widget_font(frame_display, label_countdown)
            self.t.after(100, tick_countdown)

        def start_countdown():
            if label_countdown.mode is 'until':
                if label_countdown.destination is None:
                    try:
                        d = int(spinbox_day.get())
                        mo = MONTHS_DICT[spinbox_month.get().lower()]
                        y = int(spinbox_year.get())
                        h = int(spinbox_hour.get())
                        m = int(spinbox_minute.get())
                        s = int(spinbox_second.get()) 

                        strp = '%d %s %d %d %d %d' % (d, mo, y, h, m, s)
                        strp = datetime.datetime.strptime(strp, '%d %m %Y %H %M %S')
                        label_countdown.destination = strp.timestamp()
                    except ValueError:
                        return
            else:
                now = time.time()
                if label_countdown.destination is None:
                    try:
                        h = int(spinbox_hour.get())
                        m = int(spinbox_minute.get())
                        s = int(spinbox_second.get())
                        label_countdown.destination = now + (3600*h) + (60*m) + (s)
                    except ValueError:
                        return
                else:
                    # check how long we were paused, then increase the
                    # destination by that much so the countdown doesn't skip.
                    backlog = now - label_countdown.backlog
                    label_countdown.destination += backlog
            label_countdown.is_running = True
            button_toggle.configure(text='stop')
            tick_countdown()

        def stop_countdown():
            # Store the timestamp when the countdown was paused
            # so that when it resumes, we know how long we were asleep
            label_countdown.backlog = time.time()
            label_countdown.is_running = False
            button_toggle.configure(text='start')

        def reset_countdown():
            stop_countdown()
            label_countdown.configure(text='00:00:00.0')
            label_countdown.destination = None
            label_countdown.backlog = 0

        def toggle_countdown():
            if label_countdown.is_running:
                stop_countdown()
            else:
                start_countdown()

        def reset_spinboxes():
            for item in (spinbox_hour, spinbox_minute, spinbox_second, spinbox_day, spinbox_month, spinbox_year):
                item.configure(bg=COLOR_BACKGROUND, fg=COLOR_FONT, buttonbackground=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)
                item.delete(0, 'end')

            spinbox_hour.insert(0, 0)
            spinbox_minute.insert(0, 0)
            spinbox_second.insert(0, 0)
            spinbox_day.insert(0, time.strftime('%d'))
            spinbox_month.insert(0, time.strftime('%b').lower())
            spinbox_year.insert(0, time.strftime('%Y'))

        this_instance = self.instance

        elements_until = []

        frame_display = tkinter.Frame(self.frame_applet, bg=COLOR_BACKGROUND)
        frame_controls = tkinter.Frame(self.frame_applet, bg=COLOR_BACKGROUND)
        frame_spinboxes = tkinter.Frame(frame_controls, bg=COLOR_BACKGROUND)
        label_countdown = tkinter.Label(frame_display, text='00:00:00.0', bg=COLOR_BACKGROUND, fg=COLOR_FONT)
        # Although this says 'until', the applet will start in
        # 'in' mode because I use the toggle towards the end to
        # jog everything into place.
        label_countdown.mode = 'until'
        label_countdown.destination = None
        label_countdown.backlog = 0
        label_countdown.is_running = False
        button_countdownmode = tkinter.Button(frame_controls, text='0', command=toggle_mode, bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)
        button_countdownmode.configure(width=5)
        button_toggle = tkinter.Button(frame_controls, text='start', command=toggle_countdown, bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)
        button_reset = tkinter.Button(frame_controls, text='reset', command=reset_countdown, bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)

        spinbox_hour = tkinter.Spinbox(frame_spinboxes, from_=0, to=999, width=3)
        spinbox_minute = tkinter.Spinbox(frame_spinboxes, from_=0, to=59, width=2)
        spinbox_second = tkinter.Spinbox(frame_spinboxes, from_=0, to=59, width=2)
        
        spinbox_day = tkinter.Spinbox(frame_spinboxes, from_=0, to=31, width=2)
        spinbox_month = tkinter.Spinbox(frame_spinboxes, values=MONTHS, width=4)
        spinbox_year = tkinter.Spinbox(frame_spinboxes, from_=2015, to=9999, width=4)

        reset_spinboxes()

        self.frame_applet.rowconfigure(0, weight=1)
        self.frame_applet.columnconfigure(0, weight=1)
        frame_controls.columnconfigure(1, weight=1)

        frame_display.grid(row=0, column=0, sticky='news')
        label_countdown.pack(anchor='center', expand=True)

        frame_controls.grid(row=1, column=0, sticky='ew')
        button_countdownmode.grid(row=0, column=0, sticky='ew')
        frame_spinboxes.grid(row=0, column=1, sticky='ew')
        spinbox_hour.grid(row=0, column=4)
        spinbox_minute.grid(row=0, column=5)
        spinbox_second.grid(row=0, column=6)
        # the day month year spinboxes are gridded
        # during the toggle_mode method.
        button_reset.grid(row=0, column=7)
        button_toggle.grid(row=0, column=8)

        self.elements.append(frame_display)
        self.elements.append(label_countdown)        
        self.elements.append(frame_controls)
        self.elements.append(button_countdownmode)
        self.elements.append(button_toggle)
        self.elements.append(button_reset)
        self.elements.append(frame_spinboxes)
        self.elements.append(spinbox_hour)
        self.elements.append(spinbox_minute)
        self.elements.append(spinbox_second)
        self.elements.append(spinbox_day)
        self.elements.append(spinbox_month)
        self.elements.append(spinbox_year)

        elements_until.append(spinbox_day)
        elements_until.append(spinbox_month)
        elements_until.append(spinbox_year)

        toggle_mode()
        self.frame_applet.bind('<Configure>', lambda event: self.resize_widget_font(frame_display, label_countdown))
        self.t.update()
        self.resize_widget_font(frame_display, label_countdown)


    '''stopwatch
      #####   #######    #####    ###### 
    #######   #######   #######   ### ###
      ###       ###     ### ###   ###### 
    #######     ###     #######   ###    
    #####       ###      #####    ###    
    '''
    def build_gui_stopwatch(self):
        '''
        A timer that counts upward from 0.
        '''
        def tick_stopwatch():
            if this_instance != self.instance:
                return
            if not label_stopwatch.is_running:
                return

            # started_at is reset on every press of the resume button
            # so we keep track of how much was on the clock last time
            # and add it.
            elapsed = time.time() - label_stopwatch.started_at
            elapsed += label_stopwatch.backlog

            hours, minutes, seconds = self.hms_divmod(elapsed)
            #seconds, centi = divmod(seconds, 100)
            display = '%02d:%02d:%06.3f' % (hours, minutes, seconds)
            display = display.replace('60.0', '00.0')
            previous_size = len(label_stopwatch.cget('text'))
            label_stopwatch.configure(text=display)
            if len(display) != previous_size:
                self.resize_widget_font(frame_display, label_stopwatch)
            self.t.after(10, tick_stopwatch)

        def toggle_stopwatch():
            if label_stopwatch.is_running:
                stop_stopwatch()
            else:
                start_stopwatch()

        def stop_stopwatch():
            if label_stopwatch.started_at is not None:
                # This check is important in case we press the "reset"
                # button without having started the clock yet.
                elapsed = time.time() - label_stopwatch.started_at
                # Keep track of how long the clock ran so we can
                # pick up from here when we resume.
                label_stopwatch.backlog += elapsed
            label_stopwatch.started_at = None
            label_stopwatch.is_running = False
            button_toggle.configure(text='start')
        
        def start_stopwatch():
            label_stopwatch.started_at = time.time()
            label_stopwatch.is_running = True
            button_toggle.configure(text='stop')
            tick_stopwatch()

        def reset_stopwatch():
            stop_stopwatch()
            label_stopwatch.backlog = 0
            label_stopwatch.configure(text='00:00:00.000')

        this_instance = self.instance

        frame_display = tkinter.Frame(self.frame_applet, bg=COLOR_BACKGROUND)
        frame_controls = tkinter.Frame(self.frame_applet, bg=COLOR_BACKGROUND)
        label_stopwatch = tkinter.Label(frame_display, text='00:00:00.000', bg=COLOR_BACKGROUND, fg=COLOR_FONT)
        label_stopwatch.started_at = None
        # Backlog keeps track of how much time was on the watch when we stopped it
        # So when we start it again, the counter starts from 0 and we add the backlog
        # to get a total.
        label_stopwatch.backlog = 0
        label_stopwatch.is_running = False
        button_toggle = tkinter.Button(frame_controls, text='start', command=toggle_stopwatch, bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)
        button_reset = tkinter.Button(frame_controls, text='reset', command=reset_stopwatch, bg=COLOR_DROPDOWN, activebackground=COLOR_DROPDOWN_ACTIVE)

        self.frame_applet.rowconfigure(0, weight=1)
        self.frame_applet.columnconfigure(0, weight=1)
        frame_display.grid(row=0, column=0, sticky='news')
        label_stopwatch.pack(anchor='center', expand=True)

        frame_controls.grid(row=1, column=0, sticky='ew')
        frame_controls.columnconfigure(0, weight=1)
        frame_controls.columnconfigure(1, weight=1)
        button_toggle.grid(row=0, column=1, sticky='ew')
        button_reset.grid(row=0, column=0, sticky='ew')
        
        self.elements.append(frame_display)
        self.elements.append(frame_controls)
        self.elements.append(label_stopwatch)
        self.elements.append(button_toggle)
        self.elements.append(button_reset)

        self.frame_applet.bind('<Configure>', lambda event: self.resize_widget_font(frame_display, label_stopwatch))
        # Update so that the window width and height are correct
        # when we call resize_widget_font
        self.t.update()
        self.resize_widget_font(frame_display, label_stopwatch)


    '''other
     #####    #######   ### ###   #######   ###### 
    #######   #######   ### ###   #####     ### ###
    ### ###     ###     #######   ###       ###### 
    #######     ###     ### ###   #####     ### ###
     #####      ###     ### ###   #######   ### ###
    '''

    def delete_applet_elements(self):
        self.frame_applet.unbind('<Configure>')
        for x in range(len(self.elements)):
            self.elements.pop().destroy()
        self.frame_applet.rowconfigure(0, weight=0)
        self.frame_applet.columnconfigure(0, weight=0)

    def resize_widget_font(self, parent, subordinate):
        '''
        Given a frame and a subordinate widget, resize the font of the
        widget to best fit the bounds of the frame.
        '''
        # When initializing the widgets, the width and height is usually 1, 1.
        # Must use t.update to fix everything.
        self.t.update()
        frame_w = parent.winfo_width()
        frame_h = parent.winfo_height()
        #print(frame_w, frame_h)
        text = subordinate.cget('text')
        font = self.font_by_pixels(frame_w, frame_h, text)

        subordinate.configure(font=font)

    def font_by_pixels(self, frame_w, frame_h, text):
        '''
        Given the size of a bounding box, find the best font size
        to fit text in the bounds.
        '''
        lines = text.split('\n')
        label_w = max(len(line) for line in lines)
        label_h = len(lines)

        # Padding to not look dumb
        frame_h -= 20

        # At 72 ppi, 1 point = 1 pixel height
        point_heightbased = int(frame_h / label_h)
        # but width requires involving the ratio
        point_widthbased = int(frame_w * FONT_YX_RATIO / label_w)

        point_smaller = min(point_widthbased, point_heightbased)
        point_smaller = max(point_smaller, 1)
        font = (FONT, point_smaller)

        return font

    def hms_divmod(self, amount):
        hours, minutes = divmod(amount, 3600)
        minutes, seconds = divmod(minutes, 60)

        return (hours, minutes, seconds)

    def trigger_choose_mode(self, *args):
        '''
        This method is fired when the drop-down menu item is selected.
        It will choose which build_gui method to use based on the value
        of the optionmenu text.
        '''
        mode = self.mode
        self.t.title(mode)
        method = self.mode_methods[mode]
        self.instance += 1
        self.delete_applet_elements()
        method()

c = Clock()
