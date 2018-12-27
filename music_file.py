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


import os
import struct

class PrinterMusicFile(object):
    def __init__(self):
        self.tracks = []

    @staticmethod
    def load(path):
        file = PrinterMusicFile()

        with open(path, "rb") as f:
            trackCount = struct.unpack(">B", f.read(1))[0]

            for i in range(trackCount):
                track = PrinterMusicTrack()
                channelCount = struct.unpack(">B", f.read(1))[0]

                for j in range(channelCount):
                    channel = PrinterMusicChannel()
                    noteCount = struct.unpack(">I", f.read(4))[0]

                    for k in range(noteCount):
                        t = struct.unpack(">B", f.read(1))[0]

                        if t == 0x0:
                            note = struct.unpack(">b", f.read(1))[0]
                            duration = struct.unpack(">f", f.read(4))[0]
                            channel.add_note(note, duration)
                        elif t == 0x1:
                            duration = struct.unpack(">f", f.read(4))[0]
                            channel.add_pause(duration)
                    
                    track.add_channel(channel)
            
                file.add_track(track)
        
        return file
    
    def save(self, path):
        path = os.path.realpath(path)

        if not path.endswith(".3dpm"):
            if path.endswith("."):
                path += "3dpm"
            else:
                path += ".3dpm"

        with open(path, "wb") as f:
            f.write(struct.pack(">B", len(self.tracks)))

            for track in self.tracks:
                f.write(struct.pack(">B", len(track.channels)))

                for channel in track.channels:
                    f.write(struct.pack(">I", len(channel.events)))

                    for evt in channel.events:
                        if type(evt) is PrinterMusicNote:
                            f.write(struct.pack(">B", 0x0))
                            f.write(struct.pack(">b", evt.note))
                            f.write(struct.pack(">f", evt.duration))
                        elif type(evt) is PrinterMusicPause:
                            f.write(struct.pack(">B", 0x1))
                            f.write(struct.pack(">f", evt.duration))
        
        return path

    def normalize_channel_lengths(self):
        max_length = 0

        for track in self.tracks:
            for channel in track.channels:
                if channel.duration > max_length:
                    max_length = channel.duration

        for track in self.tracks:
            for channel in track.channels:
                channel.add_pause(max_length - channel.duration)

    def __str__(self):
        lst = []

        for i, track in enumerate(self.tracks):
            lst.append("Track {}\n".format(i + 1))
            for j, channel in enumerate(track.channels):
                lst.append("  Channel {}\n".format(j + 1))
                for k, event in enumerate(channel.events):
                    if type(event) is PrinterMusicNote:
                        lst.append("    {:>6s} {:10.5f}\n".format(event.get_note_name(), event.duration))
                    else:
                        lst.append("    {:>6s} {:10.5f}\n".format("pause", event.duration))
                lst.append("\n")

        return "".join(lst)


    def add_track(self, track):
        self.tracks.append(track)

    def print_info(self):
        print("PrinterMusicFile")
        print("{} tracks".format(len(self.tracks)))

        for i, track in enumerate(self.tracks):
            print("\nTrack {}".format(i + 1))
            print("  {} channels".format(len(track.channels)))
            
            for j, channel in enumerate(track.channels):
                print("  Channel {}: {} events, {:0.5f} s".format(j + 1, len(channel.events), channel.duration))

class PrinterMusicTrack(object):
    def __init__(self):
        self.channels = []

    def add_channel(self, channel):
        self.channels.append(channel)

class PrinterMusicChannel(object):
    def __init__(self):
        self.events = []
        self.duration = 0

    def add_note(self, note, duration):
        if duration < 0:
            raise Exception("Duration cannot be negative")
        elif duration == 0:
            return

        self.events.append(PrinterMusicNote(note, duration))
        self.duration += duration
    
    def add_pause(self, duration):
        if duration < 0:
            raise Exception("Duration cannot be negative")
        elif duration == 0:
            return

        self.events.append(PrinterMusicPause(duration))
        self.duration += duration

    def __repr__(self):
        return "PrinterMusicNote" + str(self.__dict__)

class PrinterMusicEvent(object):
    pass

class PrinterMusicPause(PrinterMusicEvent):
    def __init__(self, duration):
        self.duration = duration
    
    def __repr__(self):
        return "Pause(" + str(self.duration) + ")"

class PrinterMusicNote(PrinterMusicEvent):
    def __init__(self, note, duration):
        self.note = note
        self.duration = duration
    
    def get_note_name(self):
        letters = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

        letter = letters[(self.note + 3) % 12]
        octave = (self.note // 12) - 1

        return letter + str(octave)
    
    def __repr__(self):
        return "PrinterMusicNote({note}, {duration})".format(**self.__dict__)
