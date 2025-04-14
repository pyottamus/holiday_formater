from datetime import time

class HEvent:
    __slots__ = 'event', 'time'
    event: str
    time: time
    def __init__(self, event, time):
        self.event = event
        self.time = time


class HNote:
    __slots__ = 'note',
    note: str
    def __init__(self, note):
        self.note = note

class HolidayDate:
    __slots__ = 'date', 'hevents'
    date: str
    hevents: list[HEvent | HNote]
    def __init__(self, date):
        self.date = date
        self.hevents = []

    def append(self, hevent: HEvent | HNote):
        self.hevents.append(hevent)

class Holiday:
    __slots__ = 'name', 'hdates'
    name: str
    hdates: list[HolidayDate]
    def __init__(self, name):
        self.name = name
        self.hdates = []

    def append(self, hdate: HolidayDate):
        self.hdates.append(hdate)



