import re
import sys
from datetime import time
from holiday_types import *
from enum import IntEnum

def parse_trailing_time(data: str, line: int) -> tuple[str, time]:
    pos = len(data) - 1
    if data[pos] != 'M':
        raise RuntimeError("Cannot extract time")
    pos -= 1
    if pos < 0:
        raise RuntimeError("Cannot extract time")
    if data[pos] == 'A':
        is_am = True
    elif data[pos] == 'P':
        is_am = False
    else:
        raise RuntimeError("Cannot extract time")
    pos -= 1
    if pos < 0:
        raise RuntimeError("Cannot extract time")
    while data[pos].isspace():
        pos -= 1

    if pos == 0:
        raise RuntimeError("Cannot extract time")
    m = data[pos - 1:pos + 1]
    if len(m) != 2 or not m.isdigit():
        raise RuntimeError("Cannot extract time")

    m = int(m)
    pos -= 2
    if pos < 0:
        raise RuntimeError("Cannot extract time")
    if data[pos] != ':':
        raise RuntimeError("Cannot extract time")

    pos -= 1
    if pos < 0:
        raise RuntimeError("Cannot extract time")
    sh = pos + 1
    
    if pos > 0 and data[pos - 1].isdigit():
        pos -= 1

    h = data[pos:sh]
    assert h.isdigit()
    h = int(h)
    pos -= 1
    if pos < 0:
        raise RuntimeError("Cannot extract time")
    if not data[pos].isspace():
        raise RuntimeError("Cannot extract time") 
    assert data[pos].isspace()
    txt = data[:pos].rstrip()
    if m >= 60:
        raise RuntimeError(f"{m} is not a valid number of minutes.")
    if h == 0 or h > 12:
        raise RuntimeError(f"{h} is not a valid number of hours.")

    if h == 12 and m == 0:
        suffix = 'AM' if is_am else 'PM'
        assuming = 'midnight' if is_am else 'noon'
        sys.stderr.write(f'Line {line+1}: 12:00 {suffix} is ambiguous. Assuming {assuming}.\n')
        sys.stderr.flush()

    h += ((h != 12) ^ is_am) and (12 - (24 and not is_am))
    
    return txt, time(h, m)


class KindError(Exception):
    pass


def count_leading_tabs(line: str):
    striped_line = line.lstrip('\t')
    return len(line) - len(striped_line), striped_line
class LineIter:
    def __init__(self, file):
        self.line = -1
        self.file = file
        self.next_line_pos = 0
        self.line_pos = 0
    def __iter__(self):
        for self.line, data in enumerate(self.file, self.line + 1):

            self.line_pos = self.next_line_pos
            self.next_line_pos += len(data)
            leading_tabs, data = count_leading_tabs(data)
            data = data.strip()
            if not data:
                continue
            
            if leading_tabs > 2:
                raise KindError(f"Line {self.line + 1}: Too many leading tabs ({leading_tabs})")

            yield leading_tabs, data

def suffix_unit(count: int, unit: str):
    """Formats to {count}{unit}(s), where the s is added automatically"""
    return f"{count}{unit}{'s' if (count > 1 or count == 0)  else ''}"
class Kinds(IntEnum):
    START = 0
    HOLIDAY = 1
    DATE = 2
    EVENT = 3
    NOTE = 4

    def prety(self):
        """Prety prints a `Kinds` type"""
        if self == Kinds.NOTE:
            return f"NOTE({suffix_unit(Kinds.EVENT.value - 1, ' tab')}, prefixed by '\\note')"
        return f"{self.name}({suffix_unit(self.value - 1, ' tab')})"
        
class StackAction(IntEnum):
    SHIFT = 0b000
    SHIFT_REDUCE = 0b010

SA = StackAction

class HolidayParser:
    kind: Kinds
    state: Kinds

    it: LineIter

    leading_tabs: int
    ws_count: int

    tab_size: int
    col: int
    pos: int

    @property
    def line(self):
        return self.it.line
    def __init__(self, file):
        self.it = LineIter(file)
        self.state = Kinds.START
        self.next_state = Kinds.START
        self.stack = []

    def check_if_note(self, data):
        return len(data) >= 6 and data[0:5] == "\\note" and data[5].isspace()

    def transition(self) -> tuple[SA, int]:
        leading_tabs = self.leading_tabs

        kind = self.kind
        state = self.state
        reduce : int = 0
        action : SA
        nxt : Kinds
        if state == Kinds.START:
            if kind != Kinds.HOLIDAY:
                raise KindError(f"Line {self.line + 1}: Exepected a {Kinds.HOLIDAY.prety()}, got a {kind.prety()}")
            nxt, action = Kinds.HOLIDAY, SA.SHIFT
        elif state == Kinds.HOLIDAY:
            if kind != Kinds.DATE:
                raise KindError(f"Line {self.line + 1}: Exepected a {Kinds.DATE.prety()}, got a {kind.prety()}")
            nxt, action = Kinds.DATE, SA.SHIFT
        elif state == Kinds.DATE:
            if kind != Kinds.EVENT:
                raise KindError(f"Line {self.line + 1}: Exepected a {Kinds.EVENT.prety()}, got a {kind.prety()}")
            nxt, action = Kinds.EVENT, SA.SHIFT_REDUCE
        elif state == Kinds.EVENT:
            if kind == Kinds.EVENT or kind == Kinds.NOTE:
                nxt, action = Kinds.EVENT, SA.SHIFT_REDUCE
            else:
                nxt, action = kind, SA.SHIFT
                reduce = 2 - leading_tabs
        else:
            assert False

        self.next_state = nxt
        return action, reduce
    
    def parse_holiday(self):
        self.normalize()
        return Holiday(self.data)

    def parse_date(self):
        self.normalize()
        return HolidayDate(self.data)

    def parse_event(self):
        data = self.data
        
        self.data, t = parse_trailing_time(self.data, self.line)
        self.normalize()
        return HEvent(self.data, t)
        
    def parse_note(self):
        self.data = self.data.lstrip()
        self.normalize()
        return HNote(self.data)

    def normalize(self, strip_trailing_ws=True):
        data = self.data
        self.data = re.sub('\\s+', ' ', data)
        
    def parse(self):
        for self.leading_tabs, self.data in self.it:
            self.state = self.next_state
            self.kind = Kinds(self.leading_tabs + 1)
            if self.kind == Kinds.EVENT:
                if self.check_if_note(self.data):
                    self.kind = Kinds.NOTE
                    self.data = self.data[5:]
        

            action, reduce = self.transition()
            if reduce:
                r = self.stack.pop()
                self.stack[-1].append(r)
            if reduce == 2:
                assert len(self.stack) == 1
                yield self.stack.pop()



            val = HParsers[self.kind - 1](self)
            if action == SA.SHIFT:
                self.stack.append(val)
            else:
                assert action == SA.SHIFT_REDUCE
                self.stack[-1].append(val)
        if self.stack and self.state == Kinds.EVENT:
            r = self.stack.pop()
            self.stack[0].append(r)
            yield self.stack.pop()
        else:
            raise RuntimeError("Unexpected eof")

HParsers = [HolidayParser.parse_holiday, HolidayParser.parse_date, HolidayParser.parse_event, HolidayParser.parse_note]


if __name__ == "__main__":
    f = open(r"timetable.txt", 'r', encoding="utf-8")
    
    hh = HolidayParser(f)
    lst = list(hh.parse())
    for line in lst:
        print(line.name)
        for dat in line.hdates:
            print('\t' + dat.date)
            for event in dat.hevents:
                if isinstance(event, HEvent):
                    print('\t\t' + event.event, event.time)
                else:
                    print('\t\t\t' + event.note)
