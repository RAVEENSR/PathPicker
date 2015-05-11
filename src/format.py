# Copyright (c) 2015-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
#
from __future__ import print_function

import curses
import parse
import copy
from formattedText import FormattedText

class SimpleLine(object):

    def __init__(self, formattedLine, index):
        self.formattedLine = formattedLine
        self.index = index

    def printOut(self):
        print(str(self))

    def output(self, printer):
        (minx, miny, maxx, maxy) = self.controller.getChromeBoundaries()
        maxLen = min(maxx - minx, len(str(self)))
        y = miny + self.index + self.controller.getScrollOffset()

        if (y < miny or y > maxy):
            # wont be displayed!
            return

        self.formattedLine.printText(y, minx, printer, maxLen)

    def setController(self, controller):
        self.controller = controller

    def __str__(self):
        return str(self.formattedLine)

    def isSimple(self):
        return True


class LineMatch(object):

    def __init__(self, formattedLine, result, index):
        self.formattedLine = formattedLine
        self.index = index

        (file, num, matches) = result

        self.originalFile = file
        self.file = parse.prependDir(file)
        self.num = num

        line = str(self.formattedLine)
        # save a bunch of stuff so we can
        # pickle
        self.start = matches.start()
        self.end = min(matches.end(), len(line))
        self.group = matches.group()

        # this is a bit weird but we need to strip
        # off the whitespace for the matches we got,
        # since matches like README are aggressive
        # about including whitespace. For most lines
        # this will be a no-op, but for lines like
        # "README        " we will reset end to
        # earlier
        stringSubset = line[self.start:self.end]
        strippedSubset = stringSubset.strip()
        trailingWhitespace = (len(stringSubset) - len(strippedSubset))
        self.end -= trailingWhitespace
        self.group = self.group[0:len(self.group) - trailingWhitespace]

        self.selected = False
        self.hovered = False

    def toggleSelect(self):
        self.selected = not self.selected

    def setController(self, controller):
        self.controller = controller

    def setSelect(self, val):
        self.selected = val

    def setHover(self, val):
        self.hovered = val

    def getScreenIndex(self):
        return self.index

    def getFile(self):
        return self.file

    def getDir(self):
        # for the cd command and the like. file is a string like
        # ./asd.py or ~/www/asdasd/dsada.php, so since it already
        # has the directory appended we can just split on / and drop
        # the last
        parts = self.file.split('/')[0:-1]
        return '/'.join(parts)

    def isResolvable(self):
        return not self.isGitAbbreviatedPath()

    def isGitAbbreviatedPath(self):
        # this method mainly serves as a warning for when we get
        # git-abbrievated paths like ".../" that confuse users.
        parts = self.file.split('/')
        if len(parts) and parts[0] == '...':
            return True
        return False

    def getLineNum(self):
        return self.num

    def isSimple(self):
        return False

    def getSelected(self):
        return self.selected

    def getBefore(self):
        return str(self.formattedLine)[0:self.start]

    def getAfter(self):
        return str(self.formattedLine)[self.end:]

    def getMatch(self):
        return self.group

    def __str__(self):
        return (self.getBefore() + '||' + self.getMatch()
                + '||' + self.getAfter() + '||' +
                str(self.num))

    def getDecoratorFormatting(self):
        if self.hovered and self.selected:
            attributes = (curses.COLOR_WHITE, curses.COLOR_RED, 0)
        elif self.hovered:
            attributes = (curses.COLOR_WHITE, curses.COLOR_BLUE, 0)
        elif self.selected:
            attributes = (curses.COLOR_WHITE, curses.COLOR_GREEN, 0)
        else:
            attributes = (0,0,FormattedText.UNDERLINE_ATTRIBUTE)

        return FormattedText.getSequenceForAttributes(*attributes)

    def getDecorator(self):
        if self.selected:
            return '|===>'
        return ''

    def output(self, printer):
        decorator = self.getDecorator()
        # inject the decorator and decorated style
        # into the formatted text and then simply print it out
        text = copy.deepcopy(self.formattedLine)
        decoratedMatch = (self.getDecoratorFormatting()
                          + self.getDecorator()
                          + self.getMatch())
        text.replace(self.start, self.end,
                     decoratedMatch)

        (minx, miny, maxx, maxy) = self.controller.getChromeBoundaries()
        y = miny + self.index + self.controller.getScrollOffset()

        if (y < miny or y > maxy):
            # wont be displayed!
            return

        maxLen = maxx - minx
        text.printText(y, minx, printer, maxLen)
