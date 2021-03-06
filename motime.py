#!/usr/bin/python

from __future__ import print_function,division

import argparse
import time
import serial
import curses
import sys

from operator import itemgetter

def sort_cars(state, sortby):
    return sorted(state, key=itemgetter(sortby), reverse=(sortby == 'laps'))

def update(stdscr, state):
    try:
        maxy, maxx = stdscr.getmaxyx()
        now = time.time()
        stdscr.erase()
        header = "--- Egebakken Race Timer ---\n\n"
        stdscr.addstr(0, (maxx-len(header))//2, header, curses.A_BOLD)
        stdscr.addstr("Pos  Track  Car            Laps   Last     Best     Current\n", curses.A_UNDERLINE)
        position = 1
        for car in state:
            if car['time'] > 0:
                running = now - car['time']
            else:
                running = 0
            stdscr.addstr("{:<3}  {:<5}  {:13s}  {:03}  {:7.3f}  {:7.3f}  {:7.3f}\n".format(
                position,
                car['track'],
                car['name'],
                car['laps'],
                car['lastlap'],
                car['bestlap'],
                running))
            position += 1
        stdscr.addstr(maxy-2, 0, "\nPress Q to quit, R to reset", curses.A_DIM)
        stdscr.refresh()
    except:
        return False
    else:
        try:
            ch = stdscr.getkey()
        except:
            pass
        else:
            if ch.lower() == 'q':
                return False
            elif ch.lower() == 'r':
                reset_state(state)
        return True

def reset_state(state):
    for car in state:
        car['time'] = 0
        car['laps'] = 0
        car['lastlap'] = 0
        car['bestlap'] = float('inf')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--baudrate', help='UART bitrate', type=int, default=9600)
    parser.add_argument('-d', '--device', help='UART device', default='/dev/ttyUSB0')
    parser.add_argument('-w', '--winner', help='Winning ', default='track', choices=('track', 'laps', 'bestlap'))
    parser.add_argument('drivers', help='Comma separated list of drivers')

    args = parser.parse_args()

    s = serial.Serial(args.device, args.baudrate, timeout=0.1)

    state = []
    track = 1
    for name in args.drivers.split(','):
        state.append({'name': name, 'track': track})
        track += 1
    reset_state(state)

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(1)
    curses.curs_set(0)

    while True:
        if not update(stdscr, sort_cars(state, sortby=args.winner)):
            break
        data = s.read(1)

        if len(data) > 0:
            # Log time as fast as possible
            now = time.time()

            try:
                car = int(data)
            except:
                continue
            else:
                if car == 7:
                    reset_state(state)
                    continue

                if car > len(state):
                    continue
                offset = car - 1

                if state[offset]['time'] > 0:
                    state[offset]['lastlap'] = now - state[offset]['time']
                    if state[offset]['lastlap'] < state[offset]['bestlap'] or not state[offset]['bestlap']:
                        state[offset]['bestlap'] = state[offset]['lastlap']
                    state[offset]['laps'] += 1

                state[offset]['time'] = now

    curses.curs_set(1)
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()

if __name__ == '__main__':
    main()
