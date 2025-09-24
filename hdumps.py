import os.path
from collections.abc import Iterable
from datetime import time
from holiday_types import *
from pathlib import Path
import hparse3
import io


class ControlBase:
    __slots__ = ()

class FmtLine(ControlBase):
    __slots__ = "txt"
    def __init__(self, txt):
        self.txt = txt

class TabCTRL(ControlBase):
    __slots__ = 'tab_delta'
    def __init__(self, tab_delta):
        self.tab_delta = tab_delta

IncTAB = TabCTRL(1)
DecTAB = TabCTRL(-1)


def group_fmt(lines):
    start = 0
    pos = 0
    stack = []
    is_line = True

    while True:
        if is_line:
            cur = Line
        else:
            cur = FmtLine
        is_line = not is_line
        
        while pos < len(lines):
            if not isinstance(lines[pos], cur):
                yield lines[start:pos]
                break
            pos += 1
        if pos == len(lines):
            yield lines[start:pos]
            return
        start = pos
        pos += 1
        
class Writer:
    DATA_BEGIN = ()
    DATA_END   = ()
    HOLIDAY_BEGIN = '<ol class="holiday_ol">', IncTAB
    HOLIDAY_FMT   = """<span class="holiday_title">""", IncTAB, "<li>", IncTAB, FmtLine("<h2>{}</h2>"), DecTAB, "</li>", DecTAB, "</span>", '<ol class="holiday_date_ol">', IncTAB

    DATE_BEGIN = ()
    DATE_END   = DecTAB, '</ol>'

    DATE_FMT      = '<li class="holiday_date">', IncTAB, FmtLine("<h3>{}</h3>"), DecTAB, '</li>', '<ol class="holiday_event_ol">', IncTAB

    EVENT_BEGIN = ()
    EVENT_END   = ()
    EVENT_FMT   = """<li class="holiday_event">""", IncTAB,  '<div class="holiday_event_div">', FmtLine("""<span class="holiday_event_event">{}</span>"""), FmtLine("""<span class="holiday_event_time">{}</span>"""), '</div>' ,DecTAB, "</li>"


    NOTE_BEGIN = ()
    NOTE_END   = ()
    NOTE_FMT   = '<li class="holiday_event_note">', IncTAB, FmtLine('<span colspan="2">{}</span>'), DecTAB, '</li>'

    HOLIDAY_END   = DecTAB, '</ol>', DecTAB, "</ol>"

    out_name: Path | io.TextIOBase
    header: Path | None
    trailer: Path | None
    style: Path | None
    data: Iterable[Holiday]
    embed_style: bool
    tab_level: int
    def __init__(self, data: Iterable[Holiday], out_name: str | Path | io.TextIOBase, header: str | Path | None = None, trailer: str | Path| None = None, style: str | Path| None = None, embed_style=False):
        if isinstance(out_name, str):
            out_name = Path(out_name)
        self.out_name = out_name
        self.header = Path(header) if header is not None else header
        self.trailer = Path(trailer) if trailer is not None else trailer
        self.style = Path(style) if style is not None else style
        self.data = data
        self.embed_style = embed_style
        self.tab_level = 0

    def write_header(self):
        if self.header is None:
            return

        with self.header.open('r', encoding="utf-8") as f:
            self.out.write(f.read())

    def write_trailer(self):
        if self.trailer is None:
            return
        
        with self.trailer.open('r', encoding="utf-8") as f:
            self.out.write(f.read())
    
    def write_lines(self, lines, *fmts):
        fmt_index = 0
        for ctrl in lines:
            if isinstance(ctrl, TabCTRL):
                self.tab_level += ctrl.tab_delta
                continue
            elif isinstance(ctrl, FmtLine):
                otext = ctrl.txt.format(fmts[fmt_index])
                fmt_index += 1
            else:
                assert isinstance(ctrl, str)
                otext = ctrl

            self.out.write('\t' * self.tab_level)
            self.out.write(otext)
            self.out.write('\n')
        assert fmt_index == len(fmts)

    def fmt_holiday(self, holiday):
        return holiday.name

    def fmt_date(self, hdate):
        return hdate.date

    def fmt_event_event(self, hevent):
        return hevent.event
    def fmt_event_time(self, hevent):
        t = hevent.time
        h = t.hour
        m = t.minute
        is_am = h < 12
        if not is_am:
            h -= 12
        if h == 0:
            h = 12
        return f"{h}:{m:02} {'A' if is_am else 'P'}M"

    def fmt_note(self, hnote):
        return hnote.note

    def write_event(self, hevent):
        self.write_lines(self.EVENT_BEGIN)
        event = self.fmt_event_event(hevent)
        time  = self.fmt_event_time(hevent)
        self.write_lines(self.EVENT_FMT, event, time)
        self.write_lines(self.EVENT_END)

    def write_note(self, hnote):
        self.write_lines(self.NOTE_BEGIN)
        self.write_lines(self.NOTE_FMT, self.fmt_note(hnote))
        self.write_lines(self.NOTE_END)

    def write_date(self, hdate):
        self.write_lines(self.DATE_BEGIN)
        self.write_lines(self.DATE_FMT, self.fmt_date(hdate))

        for event in hdate.hevents:
            if isinstance(event, HNote):
                self.write_note(event)
            else:
                self.write_event(event)
        


        self.write_lines(self.DATE_END)
        
    def write_holiday(self, holiday):
        self.write_lines(self.HOLIDAY_BEGIN)
        txt = self.fmt_holiday(holiday)
        self.write_lines(self.HOLIDAY_FMT, txt)

        for holiday_date in holiday.hdates:
            self.write_date(holiday_date)

        self.write_lines(self.HOLIDAY_END)

    def write_style(self):
        if self.style is None:
            return

        if not self.embed_style:
            if not isinstance(self.out_name, Path):
                raise RuntimeError("Cannot add relative link to style.css. Out file has no path")
            self.out.write(f'<link rel="stylesheet" href="{os.path.relpath(self.style, self.out_name.parent)}" />\n')
            return
        else:
            with self.style.open('r', encoding='utf-8') as f:
                self.out.write('<style type="text/css">/*<![CDATA[*/\n')
                self.out.write(f.read())
                self.out.write("/*]]>*/</style>\n")


    def write_data(self):
        self.write_lines(self.DATA_BEGIN)
        for holiday in self.data:
            self.write_holiday(holiday)
        self.write_lines(self.DATA_END)
    def _write(self):
        self.write_header()
        self.write_style()
        self.write_data()
        self.write_trailer()
    def write(self):
        if isinstance(self.out_name, Path):
            with self.out_name.open('w', encoding="utf-8") as self.out:
                self._write()
        else:
            self.out = self.out_name
            self._write()


if __name__ == "__main__":
    f = open(r"timetable.txt", 'r', encoding="utf-8")
    
    hh = hparse3.HolidayParser(f)
    w = Writer(hh.parse(), 'example.html', None, None, style, True)
    w.write()
