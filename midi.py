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
import os
import sys

parser = argparse.ArgumentParser()

parser.add_argument("input", type=str)
parser.add_argument("output", type=str, nargs="?")
parser.add_argument("--dont-normalize", action="store_true", default=False)

args = parser.parse_args(sys.argv[1:])

mid = mido.MidiFile(args.input)

file = PrinterMusicFile()
max_len = 0

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
                start = mido.tick2second(start_tick, mid.ticks_per_beat, tempo)
                duration = mido.tick2second(length, mid.ticks_per_beat, tempo)

                added = False

                for channel in ptrack.channels:
                    if channel.duration <= start:
                        channel.add_pause(start - channel.duration)
                        channel.add_note(evt.note, duration)
                        added = True
                        break
                
                if not added:
                    channel = PrinterMusicChannel()
                    channel.add_pause(start)
                    channel.add_note(evt.note, duration)
                    ptrack.add_channel(channel)

                del notes[evt.note]
    
    file.add_track(ptrack)

if not args.dont_normalize:
    file.normalize_channel_lengths()

file.print_info()
output_file = file.save(args.output if args.output else os.path.splitext(args.input)[0])

print("\nSaved to " + output_file)