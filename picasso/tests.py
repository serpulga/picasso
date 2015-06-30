import curses
from functools import wraps
import logging
import unittest

import mock

from picasso import Point, Line, Rect, Picasso


class PicassoTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PicassoTestCase, self).__init__(*args, **kwargs)

        self.logger = logging.getLogger(__name__)

    def setUp(self):
        self.window = curses.initscr()
        self.logs = []

    def tearDown(self):
        curses.endwin()

        # Print stuff after window has return to normal state.
        for l in self.logs:
            self.logger.debug(l)
        self.logs = []

    def get_at(self, x, y):
        """Returns current character in window at given position."""

        obj = self.window.inch(y, x)

        return chr(obj & 0xFF)

    def log(self, tolog):
        self.logs.append(tolog)

    def line_to_points(self, line):
        """Returns a list of points that make the passed line."""

        points = []
        if line.orientation == Line.Horizontal:
            for x in range(line.p1.x, line.p1.x + line.length + 1):
                points.append(Point(x, line.p1.y))
        elif line.orientation == Line.Vertical:
            for y in range(line.p1.y, line.p1.y + line.length + 1):
                points.append(Point(line.p1.x, y))

        return points

    def rect_to_points(self, rect):
        """Returns a list of points that make the passed rectangle."""

        points = []
        points.extend(self.line_to_points(rect.l1))
        points.extend(self.line_to_points(rect.l2))
        points.extend(self.line_to_points(rect.l3))
        points.extend(self.line_to_points(rect.l4))

        return points

    def points_to_chars(self, points):
        """
        Returns a list of the current characters in window at given positions.
        """

        return map(lambda p: self.get_at(p.x, p.y), points)

    def line_to_chars(self, line):
        """Returns a list of characters that draw the given line."""

        points = self.line_to_points(line)
        return self.points_to_chars(points)

    def rect_to_chars(self, rect):
        """Returns a list of characters that draw the give rectangle."""

        points = self.rect_to_points(rect)
        return self.points_to_chars(points)


class TestPoint(PicassoTestCase):

    def __init__(self, *args, **kwargs):
        super(TestPoint, self).__init__(*args, **kwargs)

        self.point = Point(1, 1)

    def test_draw_undraw(self):
        self.point.draw(self.window, c='?')
        chr_drawn =  self.get_at(self.point.y, self.point.x)
        self.point.undraw(self.window)
        chr_undrawn =  self.get_at(self.point.y, self.point.x)

        self.assertEqual(chr_drawn, '?')
        self.assertEqual(chr_undrawn, ' ')

    def test_get_up(self):
        up = self.point.get_up()

        self.assertEqual(self.point.x, up.x)
        self.assertEqual(self.point.y, up.y + 1)

    def test_get_down(self):
        down = self.point.get_down()

        self.assertEqual(self.point.x, down.x)
        self.assertEqual(self.point.y, down.y - 1)

    def test_get_left(self):
        left = self.point.get_left()

        self.assertEqual(self.point.x, left.x + 1)
        self.assertEqual(self.point.y, left.y)

    def test_get_right(self):
        right = self.point.get_right()

        self.assertEqual(self.point.x, right.x - 1)
        self.assertEqual(self.point.y, right.y)

    def test_touches(self):
        self.assertTrue(self.point.touches(Point(self.point.x, self.point.y)))
        self.assertFalse(self.point.touches(Point(self.point.x, self.point.y + 1)))
        self.assertFalse(self.point.touches(Point(self.point.x + 1, self.point.y)))


class TestLine(PicassoTestCase):

    def __init__(self, *args, **kwargs):
        super(TestLine, self).__init__(*args, **kwargs)

        self.h_line = Line(Point(1, 1), Point(10, 1))
        self.v_line = Line(Point(1, 1), Point(1, 10))

    def test_orientation(self):
        self.assertEqual(self.h_line.orientation, Line.Horizontal)
        self.assertEqual(self.v_line.orientation, Line.Vertical)

    def test_length(self):
        self.assertEqual(self.h_line.length, 9)
        self.assertEqual(self.v_line.length, 9)

    def test_draw_undraw(self):
        self.h_line.draw(self.window)
        h_drawn = self.line_to_chars(self.h_line)
        self.h_line.undraw(self.window)
        h_undrawn = self.line_to_chars(self.h_line)

        self.v_line.draw(self.window)
        v_drawn = self.line_to_chars(self.v_line)
        self.v_line.undraw(self.window)
        v_undrawn = self.line_to_chars(self.v_line)

        self.assertTrue(all([c == 'x' for c in h_drawn]))
        self.assertTrue(all([c == ' ' for c in h_undrawn]))

        self.assertTrue(all([c == 'x' for c in v_drawn]))
        self.assertTrue(all([c == ' ' for c in v_undrawn]))

    def test_touches(self):
        # These points will touch the lines.
        test_ok_h_points = self.line_to_points(self.h_line)
        test_ok_v_points = self.line_to_points(self.v_line)

        # Comes up with a line outside h_line.
        test_bad_h_points = self.line_to_points(Line(
            Point(self.h_line.p1.x + self.h_line.length + 1, self.h_line.p1.y),
            Point(self.h_line.p1.x + self.h_line.length + 10, self.h_line.p1.y)
        ))
        # Comes up with a line outside v_line.
        test_bad_v_points = self.line_to_points(Line(
            Point(self.h_line.p1.x, self.h_line.p1.y + self.h_line.length + 1),
            Point(self.h_line.p1.x, self.h_line.p1.y + self.h_line.length + 10)
        ))

        # All of these points touched the lines.
        self.assertTrue(all([self.h_line.touches(p) for p in test_ok_h_points]))
        self.assertTrue(all([self.v_line.touches(p) for p in test_ok_v_points]))
        # None of these points touched the lines.
        self.assertFalse(any([self.h_line.touches(p) for p in test_bad_h_points]))
        self.assertFalse(any([self.v_line.touches(p) for p in test_bad_v_points]))


class TestRect(PicassoTestCase):

    def __init__(self, *args, **kwargs):
        super(TestRect, self).__init__(*args, **kwargs)

        self.rect = Rect(p1=Point(1, 1), p2=Point(10, 10))
        self.canvas_rect = Rect(p1=Point(0, 0), p2=Point(30, 30), ltype=Line.Canvas)

    def test_draw_undraw(self):
        self.rect.draw(self.window)
        rect_drawn = self.rect_to_chars(self.rect)
        self.rect.undraw(self.window)
        rect_undrawn = self.rect_to_chars(self.rect)

        self.assertTrue(all([c == 'x' for c in rect_drawn]))
        self.assertTrue(all([c == ' ' for c in rect_undrawn]))

    def test_draw_canvas(self):
        self.canvas_rect.draw(self.window)
        canvas_drawn = self.rect_to_chars(self.canvas_rect)

        # Chars in canvas can either be '-' or '|'
        self.assertTrue(all([c in ('-', '|',) for c in canvas_drawn]))

    def test_touches(self):
        r_ok_points = self.rect_to_points(self.rect)
        # This new rect is totally outside the other.
        r_bad_points = self.rect_to_points(Rect(
            x=self.rect.l2.p1.x + 1,
            y=self.rect.l2.p1.y,
            width=10,
            height=10
        ))

        self.assertTrue(all([self.rect.touches(p) for p in r_ok_points]))
        self.assertFalse(any([self.rect.touches(p) for p in r_bad_points]))

    def test_contains(self):
        # The points creates the rect are not contained in it.
        r_bad_points = self.rect_to_points(self.rect)
        # This new rect is totally inside the other.
        r_ok_points = self.rect_to_points(Rect(
            x=self.rect.l1.p1.x + 1,
            y=self.rect.l1.p1.y + 1,
            width=self.rect.l1.length - 5,
            height=self.rect.l3.length - 5
        ))

        self.assertTrue(all([self.rect.contains(p) for p in r_ok_points]))
        self.assertFalse(any([self.rect.contains(p) for p in r_bad_points]))


# Decorator for tests that require a canvas to be drawn
# into the screen.
def draw_canvas(fn):
    @wraps(fn)
    def test_wrapper(self, *args, **kwargs):
        self.picasso.issue_command('C 20 4')
        return fn(self, *args, **kwargs)
    return test_wrapper


class TestPicasso(PicassoTestCase):

    def __init__(self, *args, **kwargs):
        super(TestPicasso, self).__init__(*args, **kwargs)

        self.picasso = Picasso()

    def test_issue_command_canvas(self):
        self.picasso.issue_command('C 20 4')
        canvas_drawn = self.rect_to_chars(Rect(
            x=0, y=0, width=20, height=4
        ))

        # Asserts the expected canvas was drawn.
        self.assertTrue(all([c in ('-', '|',) for c in canvas_drawn]))

    def test_issue_command_quit(self):
        self.assertRaises(SystemExit, self.picasso.issue_command, 'Q')

    def test_issue_command_without_canvas(self):
        with mock.patch('picasso.Picasso.warning') as warning:
            self.picasso.issue_command('B 1 1 o')

            warning.assert_called_with('Please draw a canvas before issuing other commands')

    @draw_canvas
    def test_issue_commnand_draw_line(self):
        self.picasso.issue_command('L 1 2 6 2')
        line_drawn = self.line_to_chars(Line(
            Point(1, 2), Point(6, 2)
        ))

        # Asserts expected line was drawn.
        self.assertTrue(all([c == 'x' for c in line_drawn]))

    @draw_canvas
    def test_issue_command_draw_big_line(self):
        with mock.patch('picasso.Picasso.warning') as warning:
            self.picasso.issue_command('L 1 2 100 2')

            warning.assert_called_with('Line does not fit current canvas')

    @draw_canvas
    def test_issue_command_draw_rect(self):
        self.picasso.issue_command('R 16 1 20 3')
        rect_drawn = self.rect_to_chars(Rect(
            p1=Point(16,1), p2=Point(20, 3)
        ))

        # Asserts expected rectangle was drawn.
        self.assertTrue(all([c == 'x' for c in rect_drawn]))

    @draw_canvas
    def test_issue_command_draw_big_rect(self):
        with mock.patch('picasso.Picasso.warning') as warning:
            self.picasso.issue_command('R 16 1 20 40')

            warning.assert_called_with('Rectangle does not fit current canvas')

    def test_issue_command_bucket_fill(self):
        self.picasso.issue_command('C 20 4')
        self.picasso.issue_command('L 1 2 6 2')
        self.picasso.issue_command('L 6 3 6 4')
        self.picasso.issue_command('R 16 1 20 3')
        self.picasso.issue_command('B 10 3 o')

        fill_points = (
            Point(10, 3), Point(10, 3), Point(9, 3), Point(9, 3), Point(8, 3),
            Point(8, 3), Point(7, 3), Point(7, 3), Point(7, 2), Point(7, 2),
            Point(7, 1), Point(7, 1), Point(6, 1), Point(6, 1), Point(5, 1),
            Point(5, 1), Point(4, 1), Point(4, 1), Point(3, 1), Point(3, 1),
            Point(2, 1), Point(2, 1), Point(1, 1), Point(1, 1), Point(8, 1),
            Point(8, 1), Point(9, 1), Point(9, 1), Point(10, 1), Point(10, 1),
            Point(11, 1), Point(11, 1), Point(12, 1), Point(12, 1), Point(13, 1),
            Point(13, 1), Point(14, 1), Point(14, 1), Point(15, 1), Point(15, 1),
            Point(15, 2), Point(15, 2), Point(14, 2), Point(14, 2), Point(13, 2),
            Point(13, 2), Point(12, 2), Point(12, 2), Point(11, 2), Point(11, 2),
            Point(10, 2), Point(10, 2), Point(9, 2), Point(9, 2), Point(8, 2),
            Point(8, 2), Point(11, 3), Point(11, 3), Point(12, 3), Point(12, 3),
            Point(13, 3), Point(13, 3), Point(14, 3), Point(14, 3), Point(15, 3),
            Point(15, 3), Point(15, 4), Point(15, 4), Point(14, 4), Point(14, 4),
            Point(13, 4), Point(13, 4), Point(12, 4), Point(12, 4), Point(11, 4),
            Point(11, 4), Point(10, 4), Point(10, 4), Point(9, 4), Point(9, 4),
            Point(8, 4), Point(8, 4), Point(7, 4), Point(7, 4), Point(16, 4),
            Point(16, 4), Point(17, 4), Point(17, 4), Point(18, 4), Point(18, 4),
            Point(19, 4), Point(19, 4), Point(20, 4), Point(20, 4),
        )
        empty_points = (
            # 3 points inside rect "R 16 1 20 3".
            Point(17, 2), Point(18, 2), Point(19, 2),
            # 2 rows of empty points inside lines "L 1 2 6 2" and L 6 3 6 4".
            Point(1, 3), Point(2, 3), Point(3, 3), Point(4, 3), Point(5, 3),
            Point(1, 4), Point(2, 4), Point(3, 4), Point(4, 4), Point(5, 4),
        )

        fill_drawn = self.points_to_chars(fill_points)
        empty_drawn = self.points_to_chars(empty_points)
        lines_drawn = self.line_to_chars(Line(
            Point(1, 2), Point(6, 2)
        ))
        lines_drawn.extend(self.line_to_chars(Line(
            Point(6, 3), Point(6, 4)
        )))
        rect_drawn = self.rect_to_chars(Rect(
            p1=Point(16, 1), p2=Point(20, 3)
        ))
        canvas_drawn = self.rect_to_chars(Rect(
            x=0, y=0, width=20, height=4
        ))

        # Asserts expected points where filled out with 'o'
        self.assertTrue(all([c == 'o' for c in fill_drawn]))
        # Asserts some points were not touched ie contain the ' ' character.
        self.assertTrue(all([c == ' ' for c in empty_drawn]))
        # Asserts previous drawn elements were not touched:
        # Lines are still there.
        self.assertTrue(all([c == 'x'] for c in lines_drawn))
        # Rect is still there.
        self.assertTrue(all([c == 'x'] for c in rect_drawn))
        # Canvas is still there.
        self.assertTrue(all([c in ('-', '|',) for c in canvas_drawn]))


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    unittest.main()
