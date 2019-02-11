#  bootstrap-vm - Bootstrap a VM using libvirt tools
#  Copyright (C) 2019 Jelle Besseling
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


import os
import re


# Adapted from ansible sources: https://github.com/ansible/ansible/blob/30227ace9818655f1ef8306c459664d0f160fee2/lib/ansible/modules/files/lineinfile.py
def write_changes(b_lines, dest):
    with open(dest, 'wb') as f:
        f.writelines(b_lines)


# Adapted from ansible sources: https://github.com/ansible/ansible/blob/30227ace9818655f1ef8306c459664d0f160fee2/lib/ansible/modules/files/lineinfile.py
def present(dest, regexp, line):
    b_dest = bytes(dest, encoding='utf-8')

    with open(b_dest, 'rb') as f:
        b_lines = f.readlines()

    if regexp is not None:
        bre_m = re.compile(bytes(regexp, encoding='utf-8'))

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/inserbefore has been found
    index = [-1, -1]
    b_line = bytes(line, encoding='utf-8')
    for lineno, b_cur_line in enumerate(b_lines):
        if regexp is not None:
            match_found = bre_m.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip(b'\r\n')
        if match_found:
            index[0] = lineno

    changed = False
    b_linesep = bytes(os.linesep, encoding='utf-8')
    # Exact line or Regexp matched a line in the file
    if index[0] != -1:
        b_new_line = b_line

        if not b_new_line.endswith(b_linesep):
            b_new_line += b_linesep

        if b_lines[index[0]] != b_new_line:
            b_lines[index[0]] = b_new_line
            changed = True

    # Add to the end of the file
    elif index[1] == -1:

        # If the file is not empty then ensure there's a newline before the added line
        if b_lines and not b_lines[-1][-1:] in (b'\n', b'\r'):
            b_lines.append(b_linesep)

        b_lines.append(b_line + b_linesep)
        changed = True

    if changed:
        write_changes(b_lines, dest)


# Adapted from ansible sources: https://github.com/ansible/ansible/blob/30227ace9818655f1ef8306c459664d0f160fee2/lib/ansible/modules/files/lineinfile.py
def absent(dest, regexp, line=''):
    b_dest = bytes(dest, encoding='utf-8')

    with open(b_dest, 'rb') as f:
        b_lines = f.readlines()

    if regexp is not None:
        bre_c = re.compile(bytes(regexp, encoding='utf-8'))
    found = []

    b_line = bytes(line, encoding='utf-8')

    def matcher(b_cur_line):
        if regexp is not None:
            match_found = bre_c.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip(b'\r\n')
        if match_found:
            found.append(b_cur_line)
        return not match_found

    b_lines = [l for l in b_lines if matcher(l)]
    changed = len(found) > 0

    if changed:
        write_changes(b_lines, dest)
