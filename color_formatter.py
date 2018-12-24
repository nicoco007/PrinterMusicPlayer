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


import logging

class ColorFormatter(logging.Formatter):
    def format(self, record):
        color = 37

        if record.levelno == logging.DEBUG:
            color = 34
        elif record.levelno == logging.INFO:
            color = 32
        elif record.levelno == logging.WARN:
            color = 33
        elif record.levelno == logging.ERROR:
            color = 31

        return "\033[0;{}m{}\033[0m".format(color, super().format(record))
