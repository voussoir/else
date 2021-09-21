import random
import sys
import tkinter

def clamp_abs(x, clamp):
    if x > 0:
        return min(x, clamp)
    if x < 0:
        return max(x, -clamp)
    return x

def dist(xa, ya, xb, yb):
    #distance formula
    result = (xa - xb) **2
    result += (ya - yb) ** 2
    result = result ** 0.5
    result = int(result)
    return result

def reduce_to_one(x):
    if x < 0:
        return -1

    if x > 0:
        return 1

    return 0

class dodgygame:
    def __init__(self):
        self.tk = tkinter.Tk()
        self.tk.resizable(0,0)
        self.tk.wm_title('Dodgy')
        self.tk.iconbitmap('Excl.ico')

        self.arenasize = 40
        self.arenasize_walls = self.arenasize + 2

        self.player = Player(x=0, y=0)

        self.labelframe = tkinter.Frame(self.tk)
        self.labelframe.grid(row=1, column=0, columnspan=100)
        #Allows me to center the gui units

        self.datalabel = tkinter.Label(self.tk, text='', font=('Terminal', 10))
        self.datalabel.grid(row=0, column=0, columnspan=100)

        self.stepslabel = tkinter.Label(self.labelframe, text='0', font=('Consolas', 10))
        self.stepslabel.grid(row=0, column=0)

        self.collectlabel = tkinter.Label(self.labelframe, text='0', font=('Consolas', 10), bg='#ccc')
        self.collectlabel.grid(row=0, column=1)

        self.bomblabel = tkinter.Label(self.labelframe, text='0', font=('Consolas', 10))
        self.bomblabel.grid(row=0, column=2)

        self.phantlabel = tkinter.Label(self.labelframe, text='0', font=('Consolas', 10), bg='#ccc')
        self.phantlabel.grid(row=0, column=3)

        self.poslabel = tkinter.Label(self.labelframe, text='', font=('Consolas', 10))
        self.poslabel.grid(row=0, column=4)

        self.helplabel = tkinter.Label(self.tk, text='Press H for help ->', font=('Consolas', 8))
        self.helplabel.grid(row=2, column=0, columnspan=100)

        self.consolelabel = tkinter.Label(self.tk, text='Welcome', font=('Terminal', 8), width=self.arenasize_walls, height=4)
        self.consolelabeldata = []
        self.consolelabel.configure(anchor='nw', justify='left')
        self.consolelabel.grid(row=3, column=0)

        self.tk.bind('w', lambda *args: self.move_up())
        self.tk.bind('<Up>', lambda *args: self.move_up())

        self.tk.bind('s', lambda *args: self.move_down())
        self.tk.bind('<Down>', lambda *args: self.move_down())

        self.tk.bind('a', lambda *args: self.move_left())
        self.tk.bind('<Left>', lambda *args: self.move_left())

        self.tk.bind('d', lambda *args: self.move_right())
        self.tk.bind('<Right>', lambda *args: self.move_right())

        self.tk.bind('<Button-1>', self.move_by_mouse)
        self.tk.bind('<Button-2>', lambda *args: self.middlemouse())
        self.tk.bind('<Button-3>', lambda *args: self.spawnbomb())
        self.tk.bind('j', lambda *args: self.spawnbomb())
        self.tk.bind('z', lambda *args: self.spawnbomb())
        self.tk.bind('k', lambda *args: self.spawnphantom())
        self.tk.bind('x', lambda *args: self.spawnphantom())
        self.tk.bind('r', lambda *args: self.restart())
        self.tk.bind('h', lambda *args: self.helpreel())
        self.tk.bind('<Control-w>', lambda *args: self.tk.quit())
        self.candylist = []
        self.enemylist = []
        self.bomblist = []
        self.phantomlist = []
        self.goldcandylist = []
        self.entlist = []
        self.symbol_wall ='#'
        self.symbol_floor = ' '

        self.candyspawnrate = 4

        self.enemyspawnrate = 50
        self.enemyspawnmindist = 9
        self.enemydocollide = False

        self.bombcost = 4
        self.phantomcost = 60

        self.goldcandyflashrate = 8
        self.goldcandyspawnrate = 40

        self.helplabelindex = -1
        self.helplabeltexts = [
            '<WASD>=Movement <J>=Bomb <K>=Phantom <R>=Restart ->',
            '<UDLR>=Movement <Z>=Bomb <X>=Phantom <R>=Restart ->',
            '<LMB>=Movement <RMB>=Bomb <MMB>=Phantom/Restart ->',
            f'{Player.symbol} = You ->',
            f'{Enemy.symbol} = Exclamator ->',
            f'{Candy.symbol} = Candy ->',
            f'{Bomb.symbol} = Bomb ->',
            'Avoid the Exclamators ->',
            'Collect candy to earn bombs ->',
            'Drop bombs to snare Exclamators ->',
            'Deploy phantoms to distract Exclamators ->',
            f'Phantoms have a minimum cost of {self.phantomcost} ->',
            'But deploying phantom will consume all candy ->',
            'More candy consumed = longer phantom lifespan ->',
            'Enjoy •',
            'Press H for help ->',
        ]

        self.restart()

        self.tk.update()
        width = self.tk.winfo_reqwidth()
        height = self.tk.winfo_reqheight()
        x_offset = (self.tk.winfo_screenwidth() - width) / 2
        y_offset = (self.tk.winfo_screenheight() - height) / 2
        self.tk.geometry('%dx%d+%d+%d' % (width, height, x_offset, y_offset-50))
        self.tk.mainloop()

    def collect(self, score):
        for x in range(score):
            self.collections += 1
            if self.collections % self.bombcost == 0:
                self.bombs += 1

    def do_enemy_bomb_collisions(self):
        for bomb in list(self.bomblist):
            for enemy in list(self.enemylist):
                if enemy.x == bomb.x and enemy.y == bomb.y:
                    self.bomblist.remove(bomb)
                    self.enemylist.remove(enemy)
                    self.entlist.remove(bomb)
                    self.entlist.remove(enemy)
                    self.printr(f'[ {Bomb.symbol} ] Bang')
                    break

    def do_player_enemy_collisions(self):
        for enemy in list(self.enemylist):
            if enemy.x == self.player.x and enemy.y == self.player.y:
                self.printr(f'[ {Player.symbol} ] Death')
                self.isdead = True
                self.datalabel.configure(fg='Red')

    def do_player_item_collisions(self):
        for entity in list(self.entlist):
            if entity.xy == self.player.xy:
                if isinstance(entity, Candy):
                    self.collect(entity.value)
                    self.candylist.remove(entity)
                    self.entlist.remove(entity)
                elif isinstance(entity, Goldcandy):
                    self.printr(f'[ {Goldcandy.symbol} ] Got gold')
                    self.collect(entity.value)
                    self.goldcandylist.remove(entity)
                    self.entlist.remove(entity)

    def _game_tick(self):
        self.do_player_item_collisions()
        self.do_player_enemy_collisions()
        if self.isdead:
            return

        self.move_enemies()
        self.do_player_enemy_collisions()
        if self.isdead:
            return

        self.do_enemy_bomb_collisions()

        self.ticks_elapsed += 1

        if self.ticks_elapsed % self.candyspawnrate == 0:
            self.spawncandy()

        if self.ticks_elapsed % self.goldcandyspawnrate == 0 and random.random() < 0.75:
            self.spawngoldcandy()

        if self.ticks_elapsed % self.enemyspawnrate == 0:
            enemy_count = (self.ticks_elapsed // 200) + 1
            for x in range(enemy_count):
                self.spawnenemy()

        self.expire_goldcandies()
        self.expire_phantoms()

    def game_tick(self):
        self._game_tick()
        self.redraw()

    def expire_goldcandies(self):
        for goldcandy in list(self.goldcandylist):
            goldcandy.tick(self.goldcandyflashrate)
            if goldcandy.lifespan <= 0:
                self.goldcandylist.remove(goldcandy)
                self.entlist.remove(goldcandy)

    def expire_phantoms(self):
        for phantom in list(self.phantomlist):
            if phantom.lifespan <= 0:
                self.phantomlist.remove(phantom)
                self.entlist.remove(phantom)

    def helpreel(self):
        self.helplabelindex += 1
        if self.helplabelindex > (len(self.helplabeltexts) - 1):
            self.helplabelindex = 0
        self.helplabel.configure(text=self.helplabeltexts[self.helplabelindex])

    def middlemouse(self):
        if self.isdead:
            self.restart()
        else:
            self.spawnphantom()

    def move_by_mouse(self, event):
        event.x -= 9
        event.y -= 9

        event.x /= 8
        event.y /= 12

        xdif = event.x - self.player.x
        ydif = event.y - self.player.y
        if abs(xdif) >= 0.5 or abs(ydif) >= 0.5:
            if abs(xdif) >= abs(ydif):
                if xdif > 0:
                    self.move_right()
                else:
                    self.move_left()
            else:
                if ydif > 0:
                    self.move_down()
                else:
                    self.move_up()

    def move_enemies(self):
        for enemy in self.enemylist:
            oldx = enemy.x
            oldy = enemy.y
            if self.phantomlist == []:
                enemy.approach(self.player.x, self.player.y)
            else:
                ph = self.phantomlist[0]
                enemy.approach(ph.x, ph.y)
            if self.enemydocollide:
                for otheren in self.enemylist:
                    if enemy != otheren:
                        if enemy.xy == otheren.xy:
                            self.printr(f'[ {Enemy.symbol} ] Enemy collision at {enemy.x} {enemy.y}')
                            enemy.x = oldx
                            enemy.y = oldy
            if enemy.x < 1:
                enemy.x = 1
            if enemy.x > (self.arenasize):
                enemy.x = self.arenasize

            if enemy.y < 1:
                enemy.y = 1
            if enemy.y > (self.arenasize):
                enemy.y = self.arenasize

    def move_left(self):
        if self.isdead:
            return

        if self.player.x > 1:
            self.player.x -= 1
            self.stepstaken += 1
        for phantom in self.phantomlist:
            if phantom.x < self.arenasize:
                phantom.x += 1
                phantom.lifespan -= 1

        self.game_tick()

    def move_right(self):
        if self.isdead:
            return

        if self.player.x < self.arenasize:
            self.player.x += 1
            self.stepstaken += 1
        for phantom in self.phantomlist:
            if phantom.x > 1:
                phantom.x -= 1
                phantom.lifespan -= 1

        self.game_tick()

    def move_up(self):
        if self.isdead:
            return

        if self.player.y > 1:
            self.player.y -= 1
            self.stepstaken += 1
        for phantom in self.phantomlist:
            if phantom.y < self.arenasize:
                phantom.y += 1
                phantom.lifespan -= 1

        self.game_tick()

    def move_down(self):
        if self.isdead:
            return

        if self.player.y < self.arenasize:
            self.player.y += 1
            self.stepstaken += 1
        for phantom in self.phantomlist:
            if phantom.y > 1:
                phantom.y -= 1
                phantom.lifespan -= 1

        self.game_tick()

    def printr(self, info):
        print(info)
        self.consolelabeldata.append(str(info))
        self.consolelabeldata = self.consolelabeldata[-4:]
        self.consolelabel.configure(text='\n'.join(self.consolelabeldata))

    def redraw(self):
        display = []
        display.append([self.symbol_wall] * self.arenasize_walls)
        for y in range(self.arenasize):
            display.append([self.symbol_wall] + [self.symbol_floor] * self.arenasize + [self.symbol_wall])
        display.append([self.symbol_wall] * self.arenasize_walls)

        if not self.isdead:
            display[self.player.y][self.player.x] = Player.symbol

        self.entlist.sort(key=lambda ent: ent.precedence, reverse=True)
        for entity in self.entlist:
            display[entity.y][entity.x] = entity.symbol

        display = '\n'.join(''.join(line) for line in display)
        self.datalabel.configure(text=display)
        self.stepslabel.configure(text=f'{self.stepstaken:04d} steps')
        self.collectlabel.configure(text=f'{self.collections:03d} candy')
        self.bomblabel.configure(text=f'{self.bombs:02d} bombs')
        self.poslabel.configure(text=f'{self.player.x:02d} {self.player.y:02d}')
        if self.collections >= self.phantomcost:
            self.phantlabel.configure(text='1 phantom')
        else:
            self.phantlabel.configure(text='0 phantom')

    def restart(self):
        self.printr('Resetting game.')
        self.consolelabeldata = []
        self.consolelabel.configure(text='')
        self.player.x = self.arenasize // 2
        self.player.y = self.arenasize // 2
        self.entlist = []
        self.candylist = []
        self.goldcandylist = []
        self.enemylist = []
        self.bomblist = []
        self.phantomlist = []
        self.ticks_elapsed = 0
        self.stepstaken = 0
        self.collections = 0
        self.bombs = 0
        self.isdead = False
        self.datalabel.configure(fg='Black')

        self.spawncandy()
        self.game_tick()

    def spawnbomb(self):
        goodtogo = True
        for bomb in self.bomblist:
            if bomb.xy == self.player.xy:
                goodtogo = False
        if goodtogo:
            if self.bombs > 0:
                self.bombs -= 1
                newbomb = Bomb(self.player.x, self.player.y)
                self.bomblist.append(newbomb)
                self.entlist.append(newbomb)
        self.redraw()

    def spawncandy(self, forcex=None, forcey=None):
        if forcex is None or forcey is None:
            newx = random.randint(1, self.arenasize)
            newy = random.randint(1, self.arenasize)
        else:
            newx = forcex
            newy = forcey

        new_candy = Candy(newx, newy)

        if self.player.xy == new_candy.xy:
            return

        for candy in self.candylist:
            if candy.xy == new_candy.xy:
                return

        self.printr(f'[ {Candy.symbol} ] New candy at {newx} {newy}')
        self.candylist.append(new_candy)
        self.entlist.append(new_candy)

    def spawnenemy(self):
        newx = random.randint(1, self.arenasize)
        newy = random.randint(1, self.arenasize)

        spawntries = 0
        while (dist(self.player.x, self.player.y, newx, newy) < self.enemyspawnmindist):
            newx = random.randint(1, self.arenasize)
            newy = random.randint(1, self.arenasize)
            spawntries += 1
            #print('Rerolling from', newx, newy)
            if spawntries == 10:
                print('Could not spawn enemy')
                return

        new_enemy = Enemy(newx, newy, 1)

        for enemy in self.enemylist:
            if enemy.xy == new_enemy.xy:
                return

        self.printr(f'[ {Enemy.symbol} ] New enemy at {newx} {newy}')
        self.enemylist.append(new_enemy)
        self.entlist.append(new_enemy)

    def spawngoldcandy(self, forcex=None, forcey=None):
        if forcex is None or forcey is None:
            newx = random.randint(1, self.arenasize)
            newy = random.randint(1, self.arenasize)
            spawntries = 0
            while (dist(self.player.x, self.player.y, newx, newy) < self.enemyspawnmindist):
                newx = random.randint(1, self.arenasize)
                newy = random.randint(1, self.arenasize)
                spawntries += 1
                #print('Rerolling from', newx, newy)
                if spawntries == 20:
                    #print('Could not spawn enemy')
                    return
        else:
            newx = forcex
            newy = forcey

        lifespan = dist(self.player.x, self.player.y, newx, newy)
        lifespan *= 2
        new_candy = Goldcandy(newx, newy, lifespan)

        for entity in self.entlist:
            if entity.xy == new_candy.xy:
                return

        self.printr(f'[ {Goldcandy.symbol} ] New gold candy')
        self.goldcandylist.append(new_candy)
        self.entlist.append(new_candy)

    def spawnphantom(self):
        goodtogo = True
        if self.collections < self.phantomcost:
            self.printr(f'[ {Player.symbol} ] Not enough Candy. {self.collections} / {self.phantomcost}.')
            goodtogo = False
        if self.phantomlist != []:
            goodtogo = False

        if goodtogo:
            life = 15
            self.collections = 0
            life += round(self.collections / 3)
            self.printr(f'[ {Player.symbol} ] New phantom with {life} life.')
            newphantom = Phantom(self.player.x, self.player.y, life)
            self.phantomlist.append(newphantom)
            self.entlist.append(newphantom)
        self.redraw()

class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def xy(self):
        return (self.x, self.y)

class Bomb(Entity):
    symbol = 'X'

class Candy(Entity):
    symbol = '@'
    value = 1

class Enemy(Entity):
    symbol = '!'

    def __init__(self, x, y, anger):
        super().__init__(x, y)
        self.anger = anger
        self.vel_x = 0
        self.vel_y = 0

    def approach(self, targx, targy):
        accel_x = targx - self.x
        accel_y = targy - self.y

        self.vel_x = clamp_abs(self.vel_x + accel_x, 5) * 0.85
        self.vel_y = clamp_abs(self.vel_y + accel_y, 5) * 0.85

        mag_x = abs(self.vel_x)
        mag_y = abs(self.vel_y)

        if mag_x >= 1 and mag_x > mag_y:
            self.x += reduce_to_one(self.vel_x)

        if mag_y >= 1 and mag_y >= mag_x:
            self.y += reduce_to_one(self.vel_y)

class Goldcandy(Entity):
    symbol = '$'
    value = 5

    def __init__(self, x, y, lifespan):
        super().__init__(x, y)
        self.lifespan = lifespan
        self.symbol = Goldcandy.symbol

    def tick(self, flashrate):
        self.lifespan -= 1
        if self.lifespan % flashrate == 0 or self.lifespan % flashrate == 1:
            self.symbol = Goldcandy.symbol
        else:
            self.symbol = Candy.symbol

class Player(Entity):
    symbol = 'H'

class Phantom(Entity):
    symbol = 'H'

    def __init__(self, x, y, lifespan):
        super().__init__(x, y)
        self.lifespan  = lifespan

ENTITY_PRECEDENCE = [
    Bomb,
    Player,
    Enemy,
    Phantom,
    Goldcandy,
    Candy,
]
for (index, cls) in enumerate(ENTITY_PRECEDENCE):
    cls.precedence = index

def main(argv):
    dodgygame()
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
