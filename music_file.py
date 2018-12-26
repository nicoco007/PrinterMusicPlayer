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
                    position = 0

                    for k in range(noteCount):
                        t = struct.unpack(">B", f.read(1))[0]

                        if t == 0x0:
                            note = struct.unpack(">b", f.read(1))[0]
                            duration = struct.unpack(">f", f.read(4))[0]
                            channel.add_note(note, position, duration)
                        elif t == 0x1:
                            duration = struct.unpack(">f", f.read(4))[0]
                            channel.pause_until(position + duration)
                        
                        position += duration
                    
                    track.add_channel(channel)
            
                file.add_track(track)
        
        return file
    
    def save(self, path):
        with open(path, "wb") as f:
            f.write(struct.pack(">B", len(self.tracks)))

            for track in self.tracks:
                f.write(struct.pack(">B", len(track.channels)))

                for channel in track.channels:
                    f.write(struct.pack(">I", len(channel.notes)))

                    for evt in channel.notes:
                        if type(evt) is PrinterMusicNote:
                            f.write(struct.pack(">B", 0x0))
                            f.write(struct.pack(">b", evt.note))
                            f.write(struct.pack(">f", evt.duration))
                        elif type(evt) is PrinterMusicPause:
                            f.write(struct.pack(">B", 0x1))
                            f.write(struct.pack(">f", evt.duration))

    
    def add_track(self, track):
        self.tracks.append(track)

    def print_info(self):
        print("PrinterMusicFile")
        print("{} tracks".format(len(self.tracks)))

        for i, track in enumerate(self.tracks):
            print("\nTrack {}".format(i))
            print("  {} channels".format(len(track.channels)))
            
            for j, channel in enumerate(track.channels):
                print("  Channel {}: {} events".format(j, len(channel.notes)))

class PrinterMusicTrack(object):
    def __init__(self):
        self.channels = []

    def add_channel(self, channel):
        self.channels.append(channel)

class PrinterMusicChannel(object):
    def __init__(self):
        self.notes = []
        self.current_position = 0

    def can_add_note(self, position):
        return position >= self.current_position

    def add_note(self, note, position, duration):
        if not self.can_add_note(position):
            raise Exception("Position is before last note : {} >= {}".format(position, self.current_position))

        self.pause_until(position)
        self.notes.append(PrinterMusicNote(note, duration))
        self.current_position = position + duration
    
    def pause_until(self, position):
        if not self.can_add_note(position):
            raise Exception("Position is before last note : {} >= {}".format(position, self.current_position))

        if position == self.current_position:
            return

        self.notes.append(PrinterMusicPause(position - self.current_position))
        self.current_position = position

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
        letters = {
            0: "A",
            1: "A#",
            2: "B",
            3: "C",
            4: "C#",
            5: "D",
            6: "D#",
            7: "E",
            8: "F",
            9: "F#",
            10: "G",
            11: "G#"
        }

        letter = letters[(self.note + 3) % 12]
        octave = (self.note - 12) // 12

        return letter + str(octave)
    
    def __repr__(self):
        return "PrinterMusicNote({note}, {duration})".format(**self.__dict__)
