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


import serial
import time
from threading import Thread

ser = serial.Serial('/dev/ttyACM1')
ser.baudrate = 250000

time.sleep(5)

ser.write(b"G28 Z\n")
ser.write(b"M201 Z5000\n")
ser.write(b"M203 Z5000\n")

dist = 200
inc = 0.5
dir = 1
fdr = 1000

def blah():
    global fdr
    while (ser.open):
        t = int(input("set: "))
        fdr = t

Thread(target=blah).start()

while (True):
    if not (0 <= dist + inc * dir <= 200):
        dir *= -1
    
    dist += inc * dir

    ser.write("G0 Z{} F{}\n".format(dist, fdr).encode("ascii"))

    t = ser.readline()
    while t != b"ok\n":
        t = ser.readline()