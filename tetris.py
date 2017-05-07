import curses
from random import choice, randint
from datetime import datetime, timedelta

class Block(object):
    BLOCK1 = (((0, 0), (1, 0), (0, 1), (1, 1)),)
    BLOCK2 = (((1, 1), (2, 1), (3, 1), (4, 1)),
              ((1, 1), (1, 2), (1, 3), (1, 4)))
    BLOCK3 = (((0, 1), (1, 0), (1, 1), (1, 2)),
              ((0, 1), (1, 1), (1, 2), (2, 1)),
              ((0, 0), (0, 1), (0, 2), (1, 1)),
              ((0, 1), (1, 0), (1, 1), (2, 1)))
    BLOCK4 = (((0, 0), (0, 1), (0, 2), (1, 2)),
              ((0, 1), (1, 1), (2, 0), (2, 1)),
              ((0, 0), (1, 0), (1, 1), (1, 2)),
              ((0, 0), (0, 1), (1, 0), (2, 0)))
    BLOCK5 = (((0, 0), (0, 1), (0, 2), (1, 0)),
              ((0, 0), (0, 1), (1, 1), (2, 1)),
              ((0, 2), (1, 0), (1, 1), (1, 2)),
              ((0, 0), (1, 0), (2, 0), (2, 1)))
    BLOCK6 = (((0, 1), (0, 2), (1, 0), (1, 1)),
              ((0, 0), (1, 0), (1, 1), (2, 1)))
    BLOCK7 = (((0, 0), (0, 1), (1, 1), (1, 2)),
              ((0, 1), (1, 0), (1, 1), (2, 0)))

    def __init__(self, x, y, game):
        self.shape = choice([self.BLOCK1, self.BLOCK2, self.BLOCK3, self.BLOCK4, 
                             self.BLOCK5, self.BLOCK6, self.BLOCK7])
        self.rotation = 0
        self.color = randint(1, 7)
        self.x = x
        self.y = y
        self.game = game
        cells = [(s_x + x, s_y + y) for s_x, s_y in self.shape[self.rotation]]
        if self.game.collides_with_existing_cells(cells) == True:
            exit(0)
        self.game.set_cells(cells, self.color)


    def move(self, delta_x, delta_y, rotate_clock):
        new_rotation = (self.rotation + rotate_clock) % len(self.shape)
        cells = [(s_x + self.x + delta_x, s_y + self.y + delta_y) for s_x, s_y in self.shape[new_rotation]]
        if self.game.collides_with_existing_cells(cells) == True:
            pass
        else:
            old_cells = [(s_x + self.x, s_y + self.y) for s_x, s_y in self.shape[self.rotation]]
            self.game.clear_cells(old_cells)
            self.x += delta_x
            self.y += delta_y
            self.rotation = new_rotation
            self.game.set_cells(cells, self.color)

    def fix(self):
        cells = [(s_x + self.x, s_y + self.y) for s_x, s_y in self.shape[self.rotation]]
        self.game.fix_cells(cells, self.color)



class Tetris(object):
    def __init__(self, screen, size_x, size_y):
        self.screen = screen
        self.size_x = size_x
        self.size_y = size_y
        self.lines = 0
        self.field = []
        for x in range(self.size_x):
            self.field.append(['empty'] * self.size_y)
        for x in range(self.size_x):
            for y in range(self.size_y):
                self.clear_cell(x, y)

    def draw_field(self):
        self.screen.addstr(0, 25, 'TETRIS')
        self.screen.addstr(2, 23, 'Lines: %d' % self.lines)
        self.screen.addstr(4, 23, 'ESC: End game')

        BORDER_CHAR = ord('#')
        for x in range(2 * self.size_x + 2):
            self.screen.addch(self.size_y, x, BORDER_CHAR)
        for y in range(self.size_y):
            self.screen.addch(y, 0, BORDER_CHAR)
            self.screen.addch(y, 2*self.size_x+1, BORDER_CHAR)

    def collides_with_existing_cells(self, cells):
        for c in cells:
            if c[0] < 0 or c[0] >= self.size_x:
                return True
            if c[1] >= self.size_y:
                return True
            if self.field[c[0]][c[1]] != 'empty':
                return True
        return False

    def clear_cell(self, x, y):
        self.field[x][y] = 'empty'
        self.screen.addch(y, 2 * (1 +  x), ord(' '))
        self.screen.addch(y, -1+ 2 * (1 +  x), ord(' '))

    def clear_cells(self, cells):
        for c in cells:
            self.clear_cell(c[0], c[1])


    def fix_cells(self, cells, color):
        for x, y in cells:
            self.field[x][y] = color

    def set_cell(self, x, y, color):
        if color != 'empty':
            self.screen.addch(y, 2 * (1 +  x), ord('*'), curses.color_pair(color))
            self.screen.addch(y, -1+ 2 * (1 +  x), ord('*'), curses.color_pair(color))

    def set_cells(self, cells, color):
        for c in cells:
            self.set_cell(c[0], c[1], color)


    def start(self):
        keep_running = True
        while keep_running:
            current_block = Block(self.size_x//2, 0, self)
            next_down = datetime.now() + timedelta(seconds=1)
            while True:
                c = self.screen.getch()
                if (c == 27):
                    # ESC
                    keep_running = False
                    break
                elif (c == 258):
                    # down 
                    current_block.move(delta_x=0, delta_y=1, rotate_clock=0)
                elif (c == 259):
                    # up key
                    current_block.move(delta_x=0, delta_y=0, rotate_clock=-1)
                elif (c == 260):
                    # left
                    current_block.move(delta_x=-1, delta_y=0, rotate_clock=0)
                elif (c == 261):
                    # right
                    current_block.move(delta_x=1, delta_y=0, rotate_clock=0)
                elif (c == curses.KEY_ENTER or c == 10 or c == 13):
                    for i in range(self.size_y):
                        current_block.move(delta_x=0, delta_y=1, rotate_clock=0)
                else:
                    pass

                if datetime.now() > next_down:
                    old_y = current_block.y
                    current_block.move(delta_x=0, delta_y=1, rotate_clock=0)
                    if old_y == current_block.y:
                        current_block.fix()
                        break
                    next_down += timedelta(seconds=1)

            # test for completed line
            full_lines = []
            first_clear_line = None
            for y in range(self.size_y-1, -1, -1):
                complete_line = True
                clear_line = True
                for x in range(self.size_x):
                    if self.field[x][y] == 'empty':
                        complete_line = False
                    else:
                        clear_line = False
                if clear_line:
                    first_clear_line = y
                    break
                if complete_line:
                    self.lines += 1
                    full_lines.append(y)

            if full_lines:
                self.screen.addstr(2, 23, 'Lines: %d' % self.lines)
                shift_to = full_lines[0]
                self.clear_cells([(x, shift_to) for x in range(self.size_x)])
                shift_from = full_lines[0] - 1
                while shift_from != first_clear_line:
                    if shift_from in full_lines:
                        self.clear_cells([(x, shift_from) for x in range(self.size_x)])
                        shift_from -= 1
                        continue
                    else:
                        line_to_move = [self.field[x][shift_from] for x in range(self.size_x)]
                        self.clear_cells([(x, shift_from) for x in range(self.size_x)])
                        for x in range(self.size_x):
                            self.set_cell(x, shift_to, line_to_move[x])
                            self.field[x][shift_to] = line_to_move[x]
                        shift_to -= 1
                        shift_from -= 1



def main(screen):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_MAGENTA)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_CYAN)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_WHITE)
    screen.nodelay(1)

    game = Tetris(screen=screen, size_x=10, size_y=18)
    game.draw_field()
    game.start()


if __name__ == '__main__':
    curses.wrapper(main)
