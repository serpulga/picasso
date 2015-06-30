#!/usr/bin/env python

import re
from collections import defaultdict
import curses
import locale
import sys


locale.setlocale(locale.LC_ALL, 'en_US')
code = locale.getpreferredencoding()


class Logger(object):
    def __init__(self):
        self.logs = ''

    def log(self, msg):
        self.logs += str(msg)
        self.logs += '\n'


logger = Logger()


def log(msg):
    logger.log(msg)


class Point(object):
    """
    Class representing a point.
    Can draw and un-draw itself into a window.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, window, c='o'):
        """Draw this point into the passed window"""

        window.move(self.y, self.x)
        window.addstr(c)

    def undraw(self, window):
        """Un-draw this point from the passed window"""

        window.move(self.y, self.x)
        window.addstr(' ')

    def get_up(self):
        """Returns the point that is located right above."""

        return Point(self.x, self.y - 1)

    def get_down(self):
        """Returns the point that is located right below."""

        return Point(self.x, self.y + 1)

    def get_left(self):
        """Returns the point that is located next to the left."""

        return Point(self.x - 1, self.y)

    def get_right(self):
        """Returns a point that is located next the right."""

        return Point(self.x + 1, self.y)

    def touches(self, point):
        """Simply checks if is the same point."""

        return self.__eq__(point)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.__eq__(other)

    def __repr__(self):
        return 'Point({}, {})'.format(self.x, self.y)


class Line(object):
    """
    Class representing a line.
    Can draw and un-draw itself into a window.
    """

    Horizontal = 'H'
    Vertical = 'V'
    Canvas = 'C'
    Regular = 'R'

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.orientation = self.get_orientation()

        # Decide whether or not ordering of points should change.
        if self.orientation == Line.Vertical:
            if p1.y > p2.y:
                self.p1 = p2
                self.p2 = p1
        elif self.orientation == Line.Horizontal:
            if p1.x > p2.x:
                self.p1 = p2
                self.p2 = p1

        self.length = self.get_length()

    def validate(self):
        """
        Checks whether this line is geometrically valid given the current
        constraints.
        """

        return self.orientation in (Line.Horizontal, Line.Vertical,)

    def get_orientation(self):
        """Calculates line orientation: Vertical or Horizontal."""

        if self.p1.x == self.p2.x:
            return Line.Vertical
        elif self.p1.y == self.p2.y:
            return Line.Horizontal

    def get_length(self):
        """Calculates line's length"""

        if self.orientation == Line.Horizontal:
            return self.p2.x - self.p1.x
        else:
            return self.p2.y - self.p1.y

    def draw(self, window, ltype='R'):
        """Draw this line into the passed window"""

        if not self.validate():
            return

        if ltype == Line.Canvas:
            c = '-' if self.orientation == Line.Horizontal else '|'
        else:
            c = 'x'

        window.move(self.p1.y, self.p1.x)
        # Requires a length compensation of +1, otherwise resulting
        # line is incorrect.
        if self.orientation == Line.Horizontal:
            window.hline(self.p1.y, self.p1.x, c, self.length + 1)
        else:
            window.vline(self.p1.y, self.p1.x, c, self.length + 1)

    def undraw(self, window):
        """Un-draw this line from the passed window"""

        if not self.validate():
            return

        window.move(self.p1.y, self.p1.x)
        if self.orientation == Line.Horizontal:
            window.hline(self.p1.y, self.p1.x, ' ', self.length + 1)
        else:
            window.vline(self.p1.y, self.p1.x, ' ', self.length + 1)

    def touches(self, point):
        if (self.orientation == Line.Vertical) and (point.x == self.p1.x):
            if self.p2.y >= point.y >= self.p1.y:
                # Inside the line.
                return True
        elif (self.orientation == Line.Horizontal) and (point.y == self.p1.y):
            if self.p2.x >= point.x >= self.p1.x:
                # Inside the line.
                return True
        else:
            # Definitely not contained.
            return False

    def __repr__(self):
        return 'Line({}, {})'.format(self.p1, self.p2)


class Rect(object):
    """
    Class representing a rectangle.
    Can draw and un-draw itself into/from a window.
    """

    def __init__(self, x=None, y=None, width=None, height=None, p1=None, p2=None,
                 ltype=Line.Regular):
        """
        Can be constructed either using x, y, width, height or
        p1 and p2 points.
        """

        if all(map(lambda arg: arg is not None, [x, y, width, height])):
            pass
        elif p1 is not None and p2 is not None:
            x = p1.x
            y = p1.y
            # The line themselves don't account for
            # width or height, correct by reducing 1 to both.
            width = p2.x - p1.x - 1
            height = p2.y - p1.y - 1
        else:
            raise ValueError(
                'Incorrect arguments to {} constructor, needs: {}'.format(
                self.__class__.__name__, '(x, y, width, height) or (p1, p2)'))

        # Calculates the four vertices of the canvas.
        #                l3
        #      1 ---------------------- 2
        #       |                      |
        #   l1  |                      | l2
        #       |                      |
        #      3 ---------------------- 4
        #                l4
        ###
        self.ltype = ltype

        p1 = Point(x, y)
        p2 = Point(x + width, y)
        p3 = Point(x, y + height)
        p4 = Point(x + width, y + height)

        # Adjustments to the rect
        # This makes the dimensions match the requirements.
        p11 = Point(p1.x, p1.y + 1)
        p31 = Point(p3.x, p3.y)
        self.l1 = Line(p11, p31)

        p22 = Point(p2.x + 1, p2.y + 1)
        p42 = Point(p4.x + 1, p4.y)
        self.l2 = Line(p22, p42)

        p13 = Point(p1.x, p1.y)
        p23 = Point(p2.x + 1, p2.y)
        self.l3 = Line(p13, p23)

        p34 = Point(p3.x, p3.y + 1)
        p44 = Point(p4.x + 1, p4.y + 1)
        self.l4 = Line(p34, p44)

    def draw(self, window):
        """Draw this rectangle into the passed window"""

        self.l1.draw(window, ltype=self.ltype)
        self.l2.draw(window, ltype=self.ltype)
        self.l3.draw(window, ltype=self.ltype)
        self.l4.draw(window, ltype=self.ltype)

    def undraw(self, window):
        """Un-draw this rectangle from the passed window"""

        self.l1.undraw(window)
        self.l2.undraw(window)
        self.l3.undraw(window)
        self.l4.undraw(window)

    def touches(self, point):
        """ If point touches any of its lines, returns True, else False."""

        for line in [self.l1, self.l2, self.l3, self.l4]:
            if line.touches(point):
                return True
        else:
            return False

    def contains(self, point):
        """Checks if point is inside this rectangle."""

        x_range = self.l2.p1.x > point.x > self.l1.p1.x
        y_range = self.l4.p1.y > point.y > self.l3.p1.y

        return x_range and y_range

    def __repr__(self):
        return 'Rect({}, {}, {}, {})'.format(
            self.l1, self.l2, self.l3, self.l4)


class Picasso(object):
    """
    High level interface
    Abstracts all the functionality.
    """

    # Draw canvas: C w h
    CmdCanvasRe = re.compile('^C (\d+) (\d+)$')
    # Draw line: L x1 y1 x2 y2
    CmdLineRe= re.compile('^L (\d+) (\d+) (\d+) (\d+)$')
    # Draw rectangle: R x1 y1 x2 y2
    CmdRectRe = re.compile('^R (\d+) (\d+) (\d+) (\d+)$')
    # Bucket fill: B x y color
    CmdFillRe = re.compile('^B (\d+) (\d+) (\w)$')
    # Quit: Q
    CmdQuitRe = re.compile('^Q$')

    MAX_Y = 28

    def __init__(self, *args, **kwargs):
        self.window = curses.initscr()
        self.canvas = None
        curses.curs_set(0)

        self.items = defaultdict(list)
        self.current_fill = []

    def quit(self):
        """Releases window"""

        # This is necessary to quit the program.
        curses.endwin()

    def draw_canvas(self, width, height):
        self.window.move(0, 0)
        self.canvas = Rect(x=0, y=0, width=width, height=height,
                           ltype=Line.Canvas)
        self.canvas.draw(self.window)

    def draw_line(self, line=None, p1=None, p2=None):
        if not line:
            line = Line(p1, p2)
        line.draw(self.window)

        self.items['lines'].append(line)

    def draw_rect(self, rect=None, p1=None, p2=None):
        if not rect:
            rect = Rect(p1=p1, p2=p2)
        rect.draw(self.window)

        self.items['rects'].append(rect)

    def draw_point(self, c, x=None, y=None, point=None):
        if not point:
            point = Point(x, y)
        point.draw(self.window, c)

        self.items['points'].append(point)

    def remove_canvas(self):
        self.canvas.undraw(self.window)

    def bucket_fill(self, point, c):
        if self._is_border(point):
            return

        # Paints the starting point.
        self.draw_point(c, point=point)
        point.draw(self.window, c=c)
        self.items['points'].append(point)

        # Calculates adjacent points.
        up = point.get_up()
        down = point.get_down()
        left = point.get_left()
        right = point.get_right()

        # Propagates drawing neighbours in all directions, finishes
        # when there's nothing else to draw in any direction.
        if self.canvas.contains(left):
            self.bucket_fill(left, c)

        if self.canvas.contains(up):
            self.bucket_fill(up, c)

        if self.canvas.contains(right):
            self.bucket_fill(right, c)

        if self.canvas.contains(down):
            self.bucket_fill(down, c)

    def _is_border(self, point):
        """Checks if point touches any of the current items on the window"""

        if self.canvas.touches(point):
            return True
        else:
            for item_type, items in self.items.iteritems():
                for figure in items:
                    if figure.touches(point):
                        return True
        return False

    def get_command(self):
        """Prompts for user input a returns the entered command"""

        # Let's user see the cursor only when user input is active.
        curses.curs_set(1)
        self.put_message('enter command: ')

        command = self.window.getstr()
        # Hides cursor again.
        curses.curs_set(0)
        return command

    def issue_command(self, command):
        """Validates the passed command and takes action accordingly"""

        if Picasso.CmdQuitRe.match(command):
            # Quit command:
            self.quit()
            raise SystemExit()

        elif Picasso.CmdCanvasRe.match(command):
            # Draw a canvas command:
            w, h = Picasso.CmdCanvasRe.match(command).groups()
            w = int(w)
            h = int(h)
            if w >= self.window.getmaxyx()[1]:
                self.warning('Canvas is too wide')
                return
            elif h >= Picasso.MAX_Y:
                self.warning('Canvas is too tall')
                return
            elif self.canvas:
                # Removes current canvas if any.
                self.remove_canvas()
            self.draw_canvas(int(w), int(h))

        elif not self.canvas:
            self.warning('Please draw a canvas before issuing other commands')

        elif Picasso.CmdLineRe.match(command):
            # Draw a line command:
            x1, y1, x2, y2 = Picasso.CmdLineRe.match(command).groups()
            p1 = Point(int(x1), int(y1))
            p2 = Point(int(x2), int(y2))
            line = Line(p1=p1, p2=p2)

            if (not self.canvas.contains(p1)) or (not self.canvas.contains(p2)):
               self.warning('Line does not fit current canvas')
               return

           # A valid line is one that is either vertical or horizontal.
            if line.validate():
                self.draw_line(line=line)
            else:
                self.warning('Invalid line {}'.format(line))

        elif Picasso.CmdRectRe.match(command):
            # Draw a rectangle command:
            x1, y1, x2, y2 = Picasso.CmdRectRe.match(command).groups()
            p1 = Point(int(x1), int(y1))
            p2 = Point(int(x2), int(y2))
            if self.canvas.contains(p1) and self.canvas.contains(p2):
                self.draw_rect(p1=p1, p2=p2)
            else:
                self.warning('Rectangle does not fit current canvas')

        elif Picasso.CmdFillRe.match(command):
            # Bucket fill command:
            x, y, c = Picasso.CmdFillRe.match(command).groups()
            point = Point(int(x), int(y))
            if self.canvas.contains(point):
                self.bucket_fill(point, c)
            else:
                self.warning('Point is outside current canvas')

        else:
            # Unknown command, handle smoothly.
            self.warning('Unknown command: "{}"'.format(command))

    def put_message(self, msg):
        """Puts a message in the user input space"""

        self.window.move(Picasso.MAX_Y + 2, 0)
        self.window.deleteln()
        self.window.move(Picasso.MAX_Y + 2, 0)
        self.window.addstr(msg)

    def warning(self, wrn):
        self.put_message(wrn)
        self.window.getch()


if __name__ == '__main__':
    error = None
    picasso = Picasso()
    try:
        if len(sys.argv) == 2 and sys.argv[1] == 'test':
            picasso.issue_command('C 20 4')
            picasso.issue_command('L 1 2 6 2')
            picasso.issue_command('L 6 3 6 4')
            picasso.issue_command('R 16 1 20 3')
            picasso.issue_command('B 10 3 o')
            picasso.window.getch()
        else:
            while True:
                picasso.issue_command(picasso.get_command())
    except Exception as e:
        error = str(e)
    finally:
        picasso.quit()
        if logger.logs:
            print logger.logs
        if error:
            raise
