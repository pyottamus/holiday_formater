from holiday_types import *
import hparse3
import hdumps
import argparse



if __name__ == "__main__":


    parser = argparse.ArgumentParser(description="Format high-holiday time table to html",
                                     allow_abbrev=False)
    parser.add_argument("timetable", type=str, help="input filename to process")
    parser.add_argument("output", type=str, help="output filename to write to")
    
    parser.add_argument("-s", "--style", default=None, help="stylesheet to use")
    parser.add_argument("-e", "--embed_style", action="store_true",
                        help="Whether or not to embed the stylesheet(<style>...</style>) or <link> it")

    parser.add_argument("-H", "--header", default=None, help="text to prepend to the output")
    parser.add_argument("-t", "--trailer", default=None, help="text to append to the output")
    

    args=parser.parse_args()
    with open(args.timetable, 'r', encoding="utf-8") as file:
        parser = hparse3.HolidayParser(file)
        hdumps.Writer(parser.parse(), args.output, args.header, args.trailer,
                      args.style, args.embed_style).write()
    
