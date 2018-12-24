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
import sys

parser = argparse.ArgumentParser()

parser.add_argument("--input", "-i", required=True, type=str)
parser.add_argument("--output", "-o", required=True, type=str)
parser.add_argument("--track", "-t", type=int, default=0)
parser.add_argument("--octave", "-c", type=int, default=0)

args = parser.parse_args(sys.argv[1:])

mid = mido.MidiFile(args.input)

tempo = 500000

c = 0
previous_note = None
time = 0

channels = []
channel_ticks = []
current_notes = {}
current_tick = 0

def fill_to(channel, ticks):
    pause_length = mido.tick2second(ticks - channel_ticks[channel], mid.ticks_per_beat, tempo)
    
    if pause_length > 0:
        channels[channel].append((None, pause_length))

def add_note(channel, note, duration):
    length = mido.tick2second(ticks, mid.ticks_per_beat, tempo)
    pause_length = mido.tick2second(current_tick - ticks - channel_ticks[channel], mid.ticks_per_beat, tempo)

    if channel_ticks[channel] < current_tick - ticks:
        channels[channel].append((None, pause_length))

    channels[channel].append((evt.note, length))
    channel_ticks[channel] = current_tick

for evt in mid.tracks[args.track]:
    #if evt.type == "set_tempo":
    #    tempo = evt.tempo
    
    if evt.type == "note_on":
        current_tick += evt.time

        if evt.velocity > 0:
            # note start
            current_notes[evt.note] = current_tick
        else:
            # note end
            start_tick = current_notes[evt.note]
            ticks = current_tick - start_tick

            success = False

            for i in range(len(channels)):
                if channel_ticks[i] <= current_tick - ticks:
                    add_note(i, evt.note, ticks)
                    success = True
                    break
            
            if not success:
                i = len(channels)
                channels.append([])
                channel_ticks.append(0)
                add_note(i, evt.note, ticks)

            del current_notes[evt.note]

m = max(channel_ticks)

for i in range(len(channels)):
    fill_to(i, m)

for i in range(len(channels)):
    with open(args.output + "_" + str(i), "w") as f:
        for note, duration in channels[i]:
            if note is None:
                f.write("P {}\n".format(duration))
            else:
                f.write("N {} {}\n".format(note + args.octave * 12, duration))