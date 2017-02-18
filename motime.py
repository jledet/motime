#!/usr/bin/python

from __future__ import print_function,division

import argparse
import time
import serial
import curses
import sys

def update(stdscr, state):
    try:
        now = time.time()
        stdscr.erase()
        stdscr.addstr("Egebakken Race Timer\n\n")
        stdscr.addstr("Car              Laps   Last      Best      Current\n")
        stdscr.addstr("---------------------------------------------------\n")
        for car in state:
            if car['time'] > 0:
                running = now - car['time']
            else:
                running = 0
            stdscr.addstr("{:15s}  {:03}  {:7.3f}s  {:7.3f}s  {:7.3f}s\n".format(
                car['name'],
                car['laps'],
                car['lastlap'],
                car['bestlap'],
                running))
        stdscr.refresh()
    except KeyboardInterrupt:
        return False
    except Exception as e:
        return False
    finally:
        if stdscr.getch() >= 0:
            return False
        return True

def reset_state(state):
    for car in state:
        car['time'] = 0
        car['laps'] = 0
        car['lastlap'] = 0
        car['bestlap'] = 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--baudrate', help='UART bitrate', type=int, default=9600)
    parser.add_argument('-d', '--device', help='UART device', default='/dev/ttyUSB0')
    parser.add_argument('-c', '--cars', help='Comma separated list of drivers', default='')

    args = parser.parse_args()

    s = serial.Serial(args.device, args.baudrate, timeout=0.1)

    state = []
    for name in args.cars.split(','):
        state.append({'name': name})
    reset_state(state)

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(1)
    curses.curs_set(0)

    while True:
        if not update(stdscr, state):
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
