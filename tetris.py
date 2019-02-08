#!/usr/bin/env python3

import curses
import os
import sys
from random import choice
from datetime import datetime, timedelta
import atexit
import time


class Tetrimino(object):
    """
    A geometric shape composed of four squares, connected orthogonally.
    Tetris' name for a tetromino.
    https://en.wikipedia.org/wiki/Tetromino
    """
    # Rotations are implemented according to the Game Boy
    BLOCK_O = (((1, 1), (2, 1), (1, 2), (2, 2)),)
    BLOCK_I = (((0, 1), (1, 1), (2, 1), (3, 1)),
               ((1, -1), (1, 0), (1, 1), (1, 2)))
    BLOCK_T = (((0, 1), (1, 1), (1, 2), (2, 1)),
               ((0, 1), (1, 0), (1, 1), (1, 2)),
               ((0, 1), (1, 0), (1, 1), (2, 1)),
               ((1, 0), (1, 1), (1, 2), (2, 1)))
    BLOCK_L = (((0, 1), (0, 2), (1, 1), (2, 1)),
               ((0, 0), (1, 0), (1, 1), (1, 2)),
               ((0, 1), (1, 1), (2, 0), (2, 1)),
               ((1, 0), (1, 1), (1, 2), (2, 2)))
    BLOCK_J = (((0, 1), (1, 1), (2, 1), (2, 2)),
               ((0, 2), (1, 0), (1, 1), (1, 2)),
               ((0, 0), (0, 1), (1, 1), (2, 1)),
               ((1, 0), (1, 1), (1, 2), (2, 0)))
    BLOCK_Z = (((0, 1), (1, 1), (1, 2), (2, 2)),
               ((0, 1), (0, 2), (1, 0), (1, 1)))
    BLOCK_S = (((0, 2), (1, 1), (1, 2), (2, 1)),
               ((0, 0), (0, 1), (1, 1), (1, 2)))

    def __init__(self, x, y, game):
        self.shape = choice([self.BLOCK_O, self.BLOCK_I, self.BLOCK_T, self.BLOCK_J,
                             self.BLOCK_L, self.BLOCK_Z, self.BLOCK_S])
        self.rotation = 0
        if self.shape == self.BLOCK_O:
            self.color = curses.COLOR_YELLOW
        elif self.shape == self.BLOCK_I:
            self.color = curses.COLOR_CYAN
        elif self.shape == self.BLOCK_T:
            self.color = curses.COLOR_MAGENTA
        elif self.shape == self.BLOCK_J:
            self.color = curses.COLOR_BLUE
        elif self.shape == self.BLOCK_L:
            self.color = curses.COLOR_WHITE
        elif self.shape == self.BLOCK_Z:
            self.color = curses.COLOR_RED
        elif self.shape == self.BLOCK_S:
            self.color = curses.COLOR_GREEN
        self.x = x
        self.y = y
        self.game = game
        cells = [(s_x + x, s_y + y) for s_x, s_y in self.shape[self.rotation]]
        self.game.draw_cells(cells, self.color)

    def move(self, delta_x, delta_y, rotate_clock=0):
        new_rotation = (self.rotation + rotate_clock) % len(self.shape)
        cells = [(s_x + self.x + delta_x, s_y + self.y + delta_y) for s_x, s_y in self.shape[new_rotation]]
        if self.game.collides_with_existing_cells(cells):
            pass
        else:
            old_cells = [(s_x + self.x, s_y + self.y) for s_x, s_y in self.shape[self.rotation]]
            self.game.erase_cells(old_cells)
            self.x += delta_x
            self.y += delta_y
            self.rotation = new_rotation
            self.game.draw_cells(cells, self.color)

    def move_down(self):
        self.move(delta_x=0, delta_y=1)

    def move_left(self):
        self.move(delta_x=-1, delta_y=0)

    def move_right(self):
        self.move(delta_x=1, delta_y=0)

    def rotate(self):
        self.move(delta_x=0, delta_y=0, rotate_clock=1)

    def fall_down(self):
        for i in range(self.game.size_y):
            self.move(delta_x=0, delta_y=1)

    def fix(self):
        cells = [(s_x + self.x, s_y + self.y) for s_x, s_y in self.shape[self.rotation]]
        self.game.fix_cells(cells, self.color)


class Tetris(object):
    def __init__(self, screen, size_x, size_y, game_type):
        self.screen = screen
        self.size_x = size_x
        self.size_y = size_y
        self.game_type = game_type
        self.start_time = time.time()
        if game_type == 'B':
            self._lines = 25
        else:
            self._lines = 0
        self.field = []
        self.current_block = None
        self.next_block = None
        for x in range(self.size_x):
            self.field.append(['empty'] * self.size_y)
        self.level = 0

    def drop_speed(self):
        # level:      00  01  02  03  04  05  06  07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
        drop_rates = (48, 43, 38, 33, 28, 23, 18, 13, 8, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1)
        if self.level < 29:
            drop_rate = drop_rates[self.level]
        else:
            drop_rate = 1
        return drop_rate / 60

    def cleared_line(self):
        if self.game_type == 'B':
            self._lines = max(self._lines - 1, 0)
        else:
            self._lines += 1
            if self._lines % 10 == 0:
                self.level += 1
                self.draw_level()

    def draw_score(self):
        self.screen.addstr(2, 23, 'Lines: %3d' % self._lines)

    def draw_level(self):
        self.screen.addstr(3, 23, 'Level: %3d' % self.level)

    def draw_field(self):
        self.screen.addstr(0, 25, 'TETRIS')
        self.draw_score()
        self.draw_level()
        self.screen.addstr(4, 23, 'Duration:')
        self.screen.addstr(6, 23, 'ESC / Ctrl+C: End game')

        border_char = ord('#')
        for x in range(2 * self.size_x + 2):
            self.screen.addch(self.size_y, x, border_char)
        for y in range(self.size_y):
            self.screen.addch(y, 0, border_char)
            self.screen.addch(y, 2*self.size_x+1, border_char)

    def collides_with_existing_cells(self, cells):
        for c in cells:
            if c[0] < 0 or c[0] >= self.size_x:
                return True
            if c[1] >= self.size_y:
                return True
            if c[1] == -1:
                # BLOCK_I may leave play field if rotated at initial position
                return False
            if self.field[c[0]][c[1]] != 'empty':
                return True
        return False

    def fix_cells(self, cells, color):
        for x, y in cells:
            self.field[x][y] = color

    def clear_cells(self, cells):
        for x, y in cells:
            self.field[x][y] = 'empty'

    def draw_cell(self, x, y, color):
        if color != 'empty':
            self.screen.addch(y, 2 * (1 + x), ord('*'), curses.color_pair(color))
            self.screen.addch(y, -1 + (2 * (1 + x)), ord('*'), curses.color_pair(color))

    def draw_cells(self, cells, color):
        for c in cells:
            if c[1] != -1:
                self.draw_cell(c[0], c[1], color)

    def erase_cell(self, x, y):
        self.screen.addch(y, 2 * (1 + x), ord(' '))
        self.screen.addch(y, -1 + (2 * (1 + x)), ord(' '))

    def erase_cells(self, cells):
        for c in cells:
            if c[1] != -1:
                self.erase_cell(c[0], c[1])

    def _handle_key_press(self):
        try:
            c = self.screen.getch()
            if c == 27:
                # ESC
                sys.exit()
            elif c == curses.KEY_DOWN:
                self.current_block.move_down()
            elif c == curses.KEY_UP:
                self.current_block.rotate()
            elif c == curses.KEY_LEFT:
                self.current_block.move_left()
            elif c == curses.KEY_RIGHT:
                self.current_block.move_right()
            elif c == curses.KEY_ENTER or c == 10 or c == 13 or c == 32:
                # Enter or space
                self.current_block.fall_down()
            else:
                pass
        except KeyboardInterrupt:
            # Ctrl+c
            sys.exit()

    def _remove_complete_lines(self):
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
                # no clear lines or complete lines can follow
                break
            if complete_line:
                self.cleared_line()
                full_lines.append(y)

        if full_lines:
            self.draw_score()
            shift_to = full_lines[0]
            self.erase_cells([(x, shift_to) for x in range(self.size_x)])
            self.clear_cells([(x, shift_to) for x in range(self.size_x)])
            shift_from = full_lines[0] - 1
            while shift_from != first_clear_line:
                if shift_from in full_lines:
                    self.erase_cells([(x, shift_from) for x in range(self.size_x)])
                    self.clear_cells([(x, shift_from) for x in range(self.size_x)])
                    shift_from -= 1
                    continue
                else:
                    line_to_move = [self.field[x][shift_from] for x in range(self.size_x)]
                    self.erase_cells([(x, shift_from) for x in range(self.size_x)])
                    self.clear_cells([(x, shift_from) for x in range(self.size_x)])
                    for x in range(self.size_x):
                        self.draw_cell(x, shift_to, line_to_move[x])
                        self.field[x][shift_to] = line_to_move[x]
                    shift_to -= 1
                    shift_from -= 1
            if self.game_type == 'B' and self._lines == 0:
                sys.exit()

    def run(self):
        self.next_block = Tetrimino(self.size_x + 4, 11, self)
        while True:
            self.current_block = self.next_block
            self.current_block.move(self.size_x//2 - self.current_block.x - 2, 0 - self.current_block.y)
            if self.current_block.y == 11:
                # New Tetrimino cannot be placed on field -> game over
                exit()
            self.next_block = Tetrimino(self.size_x + 4, 11, self)
            next_down = datetime.now() + timedelta(seconds=self.drop_speed())
            while True:
                self._handle_key_press()
                if datetime.now() > next_down:
                    old_y = self.current_block.y
                    self.current_block.move_down()
                    if old_y == self.current_block.y:
                        self.current_block.fix()
                        break
                    next_down += timedelta(seconds=self.drop_speed())
                self.screen.addstr(4, 23, 'Duration: %6.1fs' % (time.time() - self.start_time))
            self._remove_complete_lines()

    def goodbye(self):
        if game_type == 'B':
            self._lines = 5 - self._lines
        print('Lines cleared: %d' % self._lines)
        print('Duration: %.2fs' % (time.time() - self.start_time))
        print('Bye!')


def main(screen, game_type):
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

    game = Tetris(screen=screen, size_x=10, size_y=18, game_type=game_type)
    game.draw_field()
    atexit.register(game.goodbye)
    game.run()


if __name__ == '__main__':
    game_type = 'A'
    if len(sys.argv) > 1 and sys.argv[1] == 'B':
        game_type = 'B'

    # http://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses
    os.environ.setdefault('ESCDELAY', '0')
    curses.wrapper(main, game_type)
