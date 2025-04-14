# holiday_formater

A simple high-holiday timetable formater. Works with chabad one sites when just copy-pasted into the raw html editor menu.

# Syntax

View *timetable.txt* to see an exapmple of the syntax
See *exapmple.html* for an exapmple of the output format

Holidays have 0 leading tabs.
Dates have 1 leading tab
Events have 2 leading tab, and automatically find the time located at the end of the text
notes have 2 leading tabs and are prefixed by `\note`.

## Event time extraction

Time is automatically found in an event using the folowing algoritm

 starting from the end, find the 'AM' or 'PM', then a single space, then 2 numbers, then a colon then 1 to 2 numbers then a space. any space charector works.

# Command line

```
usage: holiday_formater.py [-h] [-s STYLE] [-e] [-H HEADER] [-t TRAILER] timetable output

Format high-holiday time table to html

positional arguments:
  timetable             input filename to process
  output                output filename to write to

options:
  -h, --help            show this help message and exit
  -s, --style STYLE     stylesheet to use
  -e, --embed_style     Whether or not to embed the stylesheet(<style>...</style>) or <link> it
  -H, --header HEADER   text to prepend to the output
  -t, --trailer TRAILER
                        text to append to the output
```