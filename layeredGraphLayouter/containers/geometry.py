

class Point(object):
    __slots__ = ('x', 'y')

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __getitem__(self, index):
        if isinstance(index, slice):
            if index.start is None and index.stop is None and index.step is None:
                return Point(self.x, self.y)
            else:
                raise IndexError()

        return self.__getattribute__(self.__slots__[index])

    def __setitem__(self, index, value):
        self.__setattr__(self.__slots__[index], value)

    def __len__(self):
        return 2

    def __iter__(self):
        return iter((self.x, self.y))

    def __repr__(self):
        return "<Point x:%f, y:%f>" % (self.x, self.y)


class Spacing(object):
    __slots__ = ('top', 'bottom', 'left', 'right')

    def __init__(self, top=0, bottom=0, left=0, right=0):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def __getitem__(self, index):
        return self.__getattribute__(self.__slots__[index])

    def __setitem__(self, index, value):
        self.__setattr__(self.__slots__[index], value)

    def __len__(self):
        return 4

    def __iter__(self):
        return iter((self.top, self.bottom, self.left, self.right))

    def __repr__(self):
        return "<Spacing t:%f, b:%f, l:%f, r:%f>" % (
            self.top, self.bottom, self.left, self.right)


class GeometryPath():
    def __init__(self, points):
        self.points = points

    def toJson(self):
        return self.points

    def __repr__(self):
        return "<% %r>" % (self.__class__.__name__, self.points)


class LRectangle():
    def __init__(self):
        self.parent = None
        self.possition = Point()
        self.margin = Spacing()
        self.size = Point()
        self.anchor = Point()

    def getAbsoluteAnchor(self) -> Point:
        """
        Returns the absolute anchor position of the port. This is the point where edges should be
        attached, relative to the containing graph. This method creates a new vector, so modifying
        the result will not affect this port in any way.

        @return a new vector with the absolute anchor position
        """
        if self.parent is None:
            return self.parent.possition + self.possition + self.anchor
        else:
            return self.possition + self.anchor

    def getMargin(self):
        return self.margin

    def getSize(self):
        return self.size

    def getPosition(self):
        return self.possition

    def getAnchor(self):
        return self.anchor

    def translate(self, x, y):
        self.possition.x += x
        self.possition.y += y
