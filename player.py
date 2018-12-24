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


from color_formatter import ColorFormatter
import logging
import serial
import sys
import threading
import time
import re

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(ColorFormatter(fmt="%(asctime)s [%(levelname)s] {%(filename)s:%(lineno)d} %(name)s: %(message)s"))

logging.basicConfig(level=logging.DEBUG, handlers=[handler])

notes = {
    43: 235, # G3
    44: 249, # G3#
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

class Player(object):
    def __init__(self, path, port):
        self.logger = logging.getLogger("{}[{}]".format(self.__class__.__name__, port))
        self.lines = open(path).readlines()
        self.port = port
        self.current_distance = 200
        self.current_direction = -1
        self.thread = None
        self.setup_thread = None

        self.setup_async()

    def setup(self):
        self.serial = serial.Serial(self.port, 250000)

        while not self.serial.readline():
            pass
        
        self.logger.info("Connected to " + self.port)

        self.send_wait("M400")
        self.send_wait("M201 Z1500")
        self.send_wait("M203 Z5000")
        self.send_wait("G28 Z0")
        self.send_wait("G0 Z200 F2000")
        self.send_wait("M400")

        self.logger.info("Ready!")

    def setup_async(self):
        self.setup_thread = threading.Thread(target=self.setup)
        self.setup_thread.start()
    
    def wait_for_setup(self):
        if self.setup_thread:
            self.setup_thread.join()
            
    def play(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
    
    def run(self):
        start_time = time.time()
        expected_time = 0

        while self.lines:
            l = self.lines.pop(0)
            
            args = l.strip().split(" ")
            cmd = args.pop(0)
            
            if cmd == "N":
                length = float(args[1])
            elif cmd == "P":
                length = float(args[0])
            
            actual_time = time.time() - start_time
            diff = expected_time - actual_time # negative if we're behind

            expected_time += length

            # skip if current event is shorted than difference
            if length < -diff:
                self.logger.warning("Skipping event")
                continue

            if abs(diff) > 0.5:
                self.logger.warning("Adjusting by {:.5f} s".format(diff))
            else:
                self.logger.debug("Adjusting by {:.5f} s".format(diff))

            length += diff
            
            if cmd == "N":
                note = int(args[0])

                if note in notes:
                    self.send_note(note, length)
                else:
                    self.logger.warning("Note {} is out of range! Waiting instead.".format(note))
                    self.send_sleep(length)
            else:
                self.send_sleep(length)
            
        self.logger.info("Done!")
                

    def send_note(self, note, duration):
        speed = notes[note]
        distance = (speed / 60.0) * duration

        if not (0 <= self.current_distance + distance * self.current_direction <= 200):
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

        while self.serial.readline() != b"ok\n":
            pass
    
    def wait_for_exit(self):
        self.thread.join()

s1 = Player("rock_0.mcode_0", "/dev/ttyACM3")
s2 = Player("rock_0.mcode_1", "/dev/ttyACM1")
s3 = Player("rock_0.mcode_2", "/dev/ttyACM0")
s4 = Player("rock_1.mcode_0", "/dev/ttyACM4")
s5 = Player("rock_1.mcode_1", "/dev/ttyACM2")

s1.wait_for_setup()
s2.wait_for_setup()
s3.wait_for_setup()
s4.wait_for_setup()
s5.wait_for_setup()

time.sleep(2)

s1.play()
s2.play()
s3.play()
s4.play()
s5.play()
