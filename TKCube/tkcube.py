import copy
import math
import random
import tkinter

class TKCube:
    def __init__(self):
        self.t = tkinter.Tk()
        self.FACES = [
        [[2, 2, 1],    [2, -2, 1],   [-2, -2, 1], [-2, 2, 1]],
        [[2, -2, 1],   [-2, -2, -1], [-2, 2, -1], [2, 2, -1]],
        [[-2, -2, 1],  [2, -2, 1],   [2, -2, -1], [-2, -2, -1]],
        [[-2, 2, 1],   [2, 2, 1],    [2, 2, -1],  [-2, 2, -1]],
        [[-2, -2, -1], [-2, 2, -1],  [-2, 2, 1],  [-2, -2, -1]],
        [[2, -2, 1],   [2, 2, 1],    [2, 2, -1],  [2, -2, -1]],
        ]
        self.INFLATE_SCALE = 8

        self.c = tkinter.Canvas(self.t, width=600, height=600, bg='#444')
        self.c.pack(fill='both', expand=True)
        self.t.bind('<Return>', self.render)
        self.is_mouse_down = False
        self.prev_mouse_x = None
        self.prev_mouse_y = None
        self.t.bind('<ButtonPress-1>', self.mouse_down)
        self.t.bind('<ButtonRelease-1>', self.mouse_up)
        self.t.bind('<Motion>', self.mouse_motion)
        self.t.bind('<Up>', lambda event: self.arbitrarymove(0, -1))
        self.t.bind('<Down>', lambda event: self.arbitrarymove(0, 1))
        self.t.bind('<Left>', lambda event: self.arbitrarymove(-1, 0))
        self.t.bind('<Right>', lambda event: self.arbitrarymove(1, 0))
        self.render()
        self.t.mainloop()

    def arbitrarymove(self, deltax, deltay):
        for face in self.FACES:
            for point in face:
                point[0] += deltax
                point[1] += deltay
        self.render()

    def mouse_down(self, event):
        self.is_mouse_down = True

    def mouse_up(self, event):
        self.is_mouse_down = False

    def mouse_motion(self, event):
        if not self.is_mouse_down:
            return
        if self.prev_mouse_x is None:
            self.prev_mouse_x = event.x
            self.prev_mouse_y = event.y
        distance = math.sqrt( ((event.x - self.prev_mouse_x) ** 2) + ((event.y - self.prev_mouse_y) ** 2) )
        self.prev_mouse_x = event.x
        self.prev_mouse_y = event.y
        print(distance)

    def center_of_square(self, face):
        x = 0; y = 0; z = 0
        for point in face:
            x += point[0]
            y += point[1]
            z += point[2]
        return [x/4, y/4, z/4]

    def plot_point_screen(self, x, y, diameter=4):
        radius = diameter / 2
        x1 = x - radius
        y1 = y - radius
        x2 = x + radius
        y2 = y + radius
        self.c.create_oval(x1, y1, x2, y2, fill='#000')

    def render(self, *event):
        self.c.delete('all')
        rendered_faces = copy.deepcopy(self.FACES)

        # Sort by depth from camera
        # The sort key is the z value of the coordinate
        # in the center of the face
        rendered_faces.sort(key=lambda face: self.center_of_square(face)[2])

        canvas_width_half = self.c.winfo_width() / 2
        canvas_height_half = self.c.winfo_height() / 2
        highest_z = max([max([point[2] for point in face]) for face in rendered_faces])
        for face in self.FACES:
            for point in face:
                x = point[0]
                y = point[1]
                z = point[2]

                # Push everything away from the camera so all z are <= 0
                z -= highest_z

                # Create vanishing point.
                distance_camera = math.sqrt((x**2) + (y**2) + (z**2))
                #if z != 0:
                #    factor = (abs(z) ** 0.2) - 1
                #    print(factor)
                #else:
                #    factor = 0
                x += x * factor
                y += y * factor
                
                # Inflate for display
                x *= self.INFLATE_SCALE
                y *= self.INFLATE_SCALE
                z *= self.INFLATE_SCALE

                # Shift the coordinates into the screen
                x += canvas_width_half
                y += canvas_height_half
                self.plot_point_screen(x, y)

        #print(rendered_faces)
t = TKCube()