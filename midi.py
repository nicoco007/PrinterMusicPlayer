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
import mido
from music_file import *
import sys

parser = argparse.ArgumentParser()

parser.add_argument("--input", "-i", required=True, type=str)
parser.add_argument("--output", "-o", required=True, type=str)
parser.add_argument("--track", "-t", type=int, default=0)
parser.add_argument("--octave", "-c", type=int, default=0)

args = parser.parse_args(sys.argv[1:])

mid = mido.MidiFile(args.input)

file = PrinterMusicFile()

for track in mid.tracks:
    tempo = 500000
    ptrack = PrinterMusicTrack()
    notes = {}
    current_tick = 0

    for evt in track:
        #if evt.type == "set_tempo":
        #    tempo = evt.tempo
        
        if evt.type == "note_on":
            current_tick += evt.time

            if evt.velocity > 0:
                # note start
                notes[evt.note] = current_tick
            else:
                # note end
                start_tick = notes[evt.note]
                length = current_tick - start_tick
                duration = mido.tick2second(length, mid.ticks_per_beat, tempo)

                added = False

                for channel in ptrack.channels:
                    if channel.can_add_note(start_tick):
                        channel.add_note(evt.note, start_tick, duration)
                        added = True
                        break
                
                if not added:
                    channel = PrinterMusicChannel()
                    channel.add_note(evt.note, start_tick, duration)
                    ptrack.add_channel(channel)

                del notes[evt.note]
    
    file.add_track(ptrack)

file.save(args.output)
loaded = PrinterMusicFile.load(args.output)

print(str(len(file.tracks)) + " " + str(len(loaded.tracks)))

for i in range(len(file.tracks)):
    print("{} {}".format(len(file.tracks[i].channels), len(loaded.tracks[i].channels)))

    for j in range(len(file.tracks[i].channels)):
        print("{} {}".format(len(file.tracks[i].channels[j].notes), len(loaded.tracks[i].channels[j].notes)))

        for k in range(len(file.tracks[i].channels[j].notes)):
            a = file.tracks[i].channels[j].notes[k]
            b = loaded.tracks[i].channels[j].notes[k]
            print("{} {:.5f} == {} {:.5f}".format(a.note if type(a) is PrinterMusicNote else "pause", a.duration, b.note if type(a) is PrinterMusicNote else "pause", b.duration))
