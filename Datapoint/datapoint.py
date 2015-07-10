import time
import tkinter


class DataPoint:
    def __init__(self, width=720, height=480, autostart=False):
        self.windowtitle = 'DataPoint'

        self.color_outbound = '#999'
        self.color_crossbar = '#bbb'
        self.color_point = '#000'
        self.crossbar_count = 10
        self.point_diameter = 4
        self.margin = 0.10
        self.origin = (0, 0)

        self._started = False
        self.t = tkinter.Tk()
        self.t.title(self.windowtitle)
        self.w = width
        self.h = height
        self.windowx = (self.screen_width-self.w) / 2
        self.windowy = ((self.screen_height-self.h) / 2) - 27
        self.geometrystring = '%dx%d+%d+%d' % (self.w, self.h,
                                               self.windowx, self.windowy)
        self.t.geometry(self.geometrystring)

        self.countdown = -1
        self.lastbump = 0
        self.t.configure(bg='#f00')
        self.t.bind('<Configure>', self.movereplot)
        self.c = tkinter.Canvas(self.t)
        self.c.pack(fill='both', expand=True)
        self.c.bind('<Motion>', self.draw_coordinateslabel)
        self.reset()
        self.previous_w = self.w
        self.previous_h = self.h
        self.clear_screen()
        self.draw_margin()
        self._started = autostart

    @property
    def screen_width(self):
        return self.t.winfo_screenwidth()

    @property
    def screen_height(self):
        return self.t.winfo_screenheight()

    @property
    def window_width(self):
        if not self._started:
            return self.w
        return self.t.winfo_width()

    @property
    def window_height(self):
        if not self._started:
            return self.h
        return self.t.winfo_height()

    def mainloop(self):
        self._started = True
        self.t.mainloop()

    def movereplot(self, *b):
        '''
        When the user expands the window, replot the graph after a
        short delay.
        '''
        previous = (self.previous_w, self.previous_h)
        current = (self.window_width, self.window_height)
        now = time.time()
        if now - self.lastbump < 0.2:
            # Go away.
            return
        if previous != current:
            # Set.
            self.previous_w = current[0]
            self.previous_h = current[1]
            self.countdown = 1
            self.lastbump = now
            self.t.after(500, self.movereplot)
            return
        if self.countdown > -1:
            # Count.
            self.countdown -= 1
            self.lastbump = now
            self.t.after(500, self.movereplot)
        if self.countdown == 0:
            # Plot.
            self.plotpoints([])
            return

    def reset(self):
        '''
        Set the DataPoint's grid attributes back to None.
        '''
        self.POINTS = set()
        self.lowest_x = None
        self.highest_x = None
        self.lowest_y = None
        self.highest_y = None
        self.span_x = None
        self.span_y = None
        self.drawable_w = None
        self.drawable_h = None
        self.margin_x = self.window_width * self.margin
        self.margin_y = self.window_height * self.margin
        self.clear_screen()
        self.draw_margin()

    def meow(self):
        return 'meow.'

    def clear_screen(self):
        '''
        Delete all canvas elements.
        '''
        self.c.delete('all')

    def draw_axes(self, x, y):
        '''
        Given the x, y pixel coordinates, draw some axes there.
        '''
        self.c.create_line(0, y, self.screen_width*2, y)
        self.c.create_line(x, 0, x, self.screen_height*2)

    def draw_margin(self):
        '''
        Draw the dark margin.
        '''
        self.c.create_rectangle(0, 0, self.window_width, self.window_height,
                                fill=self.color_outbound)
        self.c.create_rectangle(self.margin_x, self.margin_y,
                                self.window_width - self.margin_x,
                                self.window_height - self.margin_y,
                                fill='SystemButtonFace')
        self.coordinateslabel = self.c.create_text(8, 8, text='xy',
                                                   anchor='nw',
                                                   font=('Consolas', 10))

    def draw_labels(self):
        '''
        Draw the text labels along the axes.
        '''
        if len(self.POINTS) == 0:
            return
        if len(self.POINTS) == 1:
            p = next(iter(self.POINTS))
            if p == self.origin:
                return
            lp = self.transform_coord(*p)
            self.c.create_text(lp[0], lp[1]+10, text=str(p))
            return

        low = self.transform_coord(self.lowest_x, self.lowest_y)
        low_x = low[0]
        low_y = low[1]
        hi = self.transform_coord(self.highest_x, self.highest_y)
        hi_x = hi[0]
        hi_y = hi[1]

        if self.highest_x != self.lowest_x:
            # LOW X
            self.c.create_text(low_x+5, low_y+5,
                               text=str(round(self.lowest_x, 4)), anchor='nw')
            # FAR X
            self.c.create_text(hi_x+5, low_y+5,
                               text=str(round(self.highest_x, 4)), anchor='nw')

            increment_x = (self.highest_x - self.lowest_x) / self.crossbar_count
            # crossbartop = (self.window_height - self.margin_y) - 5
            # crossbarbot = (self.window_height - self.margin_y) + 5
            crossbartop = self.margin_y
            crossbarbot = self.window_height - self.margin_y
            for x in range(1, self.crossbar_count):
                x = (x * increment_x) + self.lowest_x
                p = self.transform_coord(x, self.lowest_y)
                self.c.create_line(p[0], crossbartop, p[0], crossbarbot,
                                   fill=self.color_crossbar)
                x = str(round(x, 3))
                self.c.create_text(p[0], low_y+5, text=x, anchor='n')

        if self.highest_y != self.lowest_y:
            # LOW Y
            self.c.create_text(low_x-5, low_y,
                               text=str(round(self.lowest_y, 4)), anchor='se')
            # UPPER Y
            self.c.create_text(low_x-5, hi_y,
                               text=str(round(self.highest_y, 4)), anchor='e')
            increment_y = (self.highest_y - self.lowest_y) / self.crossbar_count
            # crossbarlef = self.margin_x - 5
            # crossbarrgt = self.margin_x + 5
            crossbarlef = self.margin_x
            crossbarrgt = self.window_width - self.margin_x
            for y in range(1, self.crossbar_count):
                y = (y * increment_y) + self.lowest_y
                p = self.transform_coord(self.lowest_x, y)
                self.c.create_line(crossbarlef, p[1], crossbarrgt, p[1],
                                   fill=self.color_crossbar)
                y = str(round(y, 3))
                self.c.create_text(low_x-5, p[1], text=y, anchor='e')

    def draw_coordinateslabel(self, event):
        if len(self.POINTS) < 2:
            return
        l = self.transform_coord(event.x, event.y, reverse=True)
        l = '%03.12f, %03.12f' % l
        self.c.itemconfigure(self.coordinateslabel, text=l)

    def transform_coord(self, x, y, reverse=False):
        '''
        Given an x,y coordinate for a point, return the screen coordinates
        or vice-versa.
        '''
        if not reverse:
            if len(self.POINTS) == 1:
                return (self.window_width/2, self.window_height/2)
            # Get percentage of the span
            x = ((x) - self.lowest_x) / self.span_x
            y = ((y) - self.lowest_y) / self.span_y
            # Flip y
            y = 1 - y
            # Use the percentage to get a location on the board
            x *= self.drawable_w
            y *= self.drawable_h
            # Put into drawing area
            x += self.margin_x
            y += self.margin_y

        else:
            if self.highest_x != self.lowest_x:
                x -= self.margin_x
                x /= self.drawable_w
                x = (x * self.span_x) + self.lowest_x
            else:
                x = self.lowest_x

            if self.highest_y != self.lowest_y:
                y -= self.margin_y
                y /= self.drawable_h
                y = 1 - y
                y = (y * self.span_y) + self.lowest_y
            else:
                y = self.lowest_y

        return (x, y)

    def plotpoints(self, points=[]):
        '''
        Plot points onto the canvas.
        var points = list, where each element is a 2-length tuple, where [0]
        is x and [1] is y coordinate.
        '''
        for point in points:
            self.POINTS.add(tuple(point))

        self.clear_screen()
        self.draw_margin()
        if len(self.POINTS) == 0:
            return

        xs = [point[0] for point in self.POINTS]
        ys = [point[1] for point in self.POINTS]
        self.lowest_x = min(xs)
        self.highest_x = max(xs)
        self.lowest_y = min(ys)
        self.highest_y = max(ys)

        self.span_x = abs(self.highest_x - self.lowest_x)
        self.span_y = abs(self.highest_y - self.lowest_y)
        if self.span_x == 0:
            self.span_x = 1
        if self.span_y == 0:
            self.span_y = 1
        self.drawable_w = self.window_width - (2 * self.margin_x)
        self.drawable_h = self.window_height - (2 * self.margin_y)

        self.draw_labels()
        if len(self.POINTS) > 1 or self.origin in self.POINTS:
            p = self.transform_coord(*self.origin)
            self.draw_axes(*p)

        for point in self.POINTS:
            p = self.transform_coord(point[0], point[1])
            x = p[0]
            y = p[1]

            r = self.point_diameter / 2
            self.c.create_oval(x-r, y-r, x+r, y+r, fill=self.color_point,
                               outline=self.color_point)
            self.c.update()

    def plotpoint(self, x, y):
        self.plotpoints([[x, y]])

    def set_origin(self, x, y):
        self.origin = (x, y)
        self.plotpoints([])


def example(function):
    dp = DataPoint()
    points = list(range(100))
    points = [[p, function(p)] for p in points]
    dp.plotpoints(points)
    dp.mainloop()


def example2():
    dp = DataPoint()
    points = [
        (1, 2), (2, 20), (3, 2), (4, 4), (5, 1), (6, 1), (7, 3), (8, 1),
        (9, 1), (10, 1), (11, 1), (12, 2), (13, 5), (14, 306), (15, 60),
        (16, 543), (17, 225), (18, 616), (19, 1546), (20, 1523), (21, 1578),
        (22, 1423), (23, 1257), (24, 1612), (25, 1891), (26, 2147), (27, 2154),
        (28, 2286), (29, 2411), (30, 2412), (31, 2382), (32, 2954), (33, 3051),
        (34, 3240), (35, 3794), (36, 2762), (37, 2090), (38, 2424), (39, 3448),
        (40, 4039), (41, 4115), (42, 3885), (43, 3841), (44, 4563), (45, 4974),
        (46, 1816), (47, 1631), (48, 1924), (49, 2024), (50, 2381), (51, 2253),
        (52, 2579), (53, 2713), (54, 3151), (55, 3380), (56, 4144), (57, 5685),
        (58, 5373), (59, 5571), (60, 5383), (61, 5967), (62, 8577), (63, 8196),
        (64, 8120), (65, 8722), (66, 8752), (67, 9841), (68, 10929),
        (69, 12585), (70, 11963), (71, 12632), (72, 11186), (73, 11122),
        (74, 13547), (75, 13376), (76, 13253), (77, 15094), (78, 14401),
        (79, 14577), (80, 15264), (81, 14621), (82, 13479), (83, 14028),
        (84, 14514), (85, 15345), (86, 23059), (87, 26502), (88, 23460),
        (89, 19223), (90, 19972), (91, 17815), (92, 21154), (93, 22606),
        (94, 22320), (95, 23703), (96, 40752), (97, 21730), (98, 27637),
        (99, 45931), (100, 18443), (101, 20048), (102, 18097), (103, 11430)
    ]
    dp.plotpoints(points)
    dp.mainloop()


def examplefunction(x):
    x -= 50
    x *= 0.1
    y = 1 / (1 + (2.718 ** -x))
    return y


def examplefunction2(x):
    return x ** 2
