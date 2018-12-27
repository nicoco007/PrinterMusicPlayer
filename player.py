#    PrinterMusicPlayer
#    Copyright © 2018  Nicolas Gnyra

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
from color_formatter import ColorFormatter
import logging
from music_file import *
import serial
import sys
import threading
import time
import re
import sys

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(ColorFormatter(fmt="%(asctime)s [%(levelname)s] {%(filename)s:%(lineno)d} %(name)s: %(message)s"))

logging.basicConfig(level=logging.DEBUG, handlers=[handler])

parser = argparse.ArgumentParser()

parser.add_argument("file", type=str)
parser.add_argument("--printer", "-p", nargs="+", type=str, required=True)

args = parser.parse_args(sys.argv[1:])

notes = {
    43: 235, # G2
    44: 249, # G2#
    45: 264, # A3
    46: 280, # A3#
    47: 296, # B3
    48: 314, # C4
    49: 333, # C4#
    50: 353, # D4
    51: 373, # D4#
    52: 396, # E4
    53: 419, # F4
    54: 444, # F4#
    55: 471, # G4
    56: 498, # G4#
    57: 528, # A4
    58: 559, # A4#
    59: 593, # B4
    60: 627, # C5
    61: 668, # C5#
    62: 706, # D5
    63: 747, # D5#
    64: 793, # E
    65: 839, # F
    66: 892, # F#
    67: 943, # G
    68: 999, # G#
    69: 1060, # A
    70: 1121, # A#
    71: 1190, # B
    72: 1260, # C
    73: 1335, # C#
    74: 1413, # D
    75: 1499, # D#
    76: 1585, # E
    77: 1680, # F
    78: 1781, # F#
    79: 1888, # G
    80: 2000, # G#
    81: 2119, # A
    82: 2250, # A#
    83: 2390, # B
    84: 2520, # C
    85: 2675, # C#
    86: 2830, # D
    87: 3000, # D#
    88: 3180, # E
    89: 3370, # F
    90: 3550, # F#
    91: 3760, # G
    92: 3980  # G#
}

class PlayerCoordinator(object):
    def __init__(self, file_path):
        self.file = PrinterMusicFile.load(file_path)
        self.players = []
    
    def add_player(self, track_id, channel_id, port, baudrate = 250000):
        self.players.append(Player(self.file.tracks[track_id].channels[channel_id], port, baudrate))
    
    def play(self, delay = 2):
        for player in self.players:
            player.setup_async()
        
        for player in self.players:
            player.wait_for_setup()
        
        time.sleep(delay)

        for player in self.players:
            player.play()

class Player(object):
    MIN_DIST = 0
    MAX_DIST = 200
    START = 200
    START_DIR = -1

    def __init__(self, channel, port, baudrate = 250000):
        self.logger = logging.getLogger("{}[{}]".format(self.__class__.__name__, port))
        self.channel = channel
        self.port = port
        self.baudrate = baudrate
        self.current_distance = Player.START
        self.current_direction = Player.START_DIR
        self.thread = None
        self.setup_thread = None

    def setup(self):
        self.serial = serial.Serial(self.port, self.baudrate)

        # wait for response from printer
        while not self.serial.readline():
            pass
        
        self.logger.info("Connected to " + self.port)

        self.send_wait("M400")
        self.send_wait("M201 Z1500") # max acceleration
        self.send_wait("M203 Z5000") # max feedrate
        self.send_wait("G28 Z0")
        self.send_wait("G0 {} F2000".format(Player.START))
        self.send_wait("M400")

        self.logger.info("Ready!")

    def setup_async(self):
        self.setup_thread = threading.Thread(target=self.setup)
        self.setup_thread.start()

    def sanity_check(self):
        for event in self.channel.notes:
            if type(event) is PrinterMusicNote and not min(notes.keys()) <= event.note <= max(notes.keys()):
                print("{} is out of range!".format(event.note))
        
        print("Sanity check complete")
    
    def wait_for_setup(self):
        if self.setup_thread:
            self.setup_thread.join()
            
    def play(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
    
    def run(self):
        start_time = time.time()
        expected_time = 0

        for event in self.channel.notes:
            length = event.duration
            actual_time = time.time() - start_time
            diff = expected_time - actual_time # negative if we're behind

            expected_time += length

            # skip if current event is shorted than difference
            if length < -diff:
                self.logger.warning("Skipping event")
                continue

            # warn if over 500 ms
            if abs(diff) > 0.5:
                self.logger.warning("Adjusting by {:.5f} s".format(diff))
            else:
                self.logger.debug("Adjusting by {:.5f} s".format(diff))

            length += diff
            
            if type(event) == PrinterMusicNote:
                if event.note in notes:
                    self.send_note(event.note, length)
                else:
                    self.logger.warning("Note {} is out of range! Waiting instead.".format(event.note))
                    self.send_sleep(length)
            else:
                self.send_sleep(length)
            
        self.logger.info("Done!")
                

    def send_note(self, note, duration):
        speed = notes[note]
        distance = (speed / 60.0) * duration # feedrate is in mm/min

        if not (Player.MIN_DIST <= self.current_distance + distance * self.current_direction <= Player.MAX_DIST):
            self.current_direction *= -1

        self.current_distance += distance * self.current_direction

        self.send_wait("G0 Z{} F{}".format(self.current_distance, speed))
        self.send_wait("M400")
    
    def send_sleep(self, duration):
        self.send_wait("G4 P{}".format(duration * 1000))

    def send(self, cmd):
        self.logger.debug("SEND " + cmd)
        self.serial.write((cmd.strip() + "\n").encode("ascii"))

    def send_wait(self, cmd):
        self.send(cmd)

        # wait for acknowledgement
        while self.serial.readline() != b"ok\n":
            pass
    
    def wait_for_exit(self):
        self.thread.join()

coord = PlayerCoordinator(args.file)

for printer in args.printer:
    if not len(printer.split(":")) == 3:
        continue

    track, channel, port = printer.split(":")
    coord.add_player(int(track), int(channel), port)

coord.play()
