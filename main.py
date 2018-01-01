# Copyright (C) 2018 0x9fff00

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import argparse, json, os, subprocess, sys
from download_helper.downloaders import curseforge_minecraft

def get_mod_data(mod, mc_version, release_phase):
    mod_data = curseforge_minecraft.get_data(mod, mc_version, release_phase)

    if mod_data == None and release_phase == 'Release':
        mod_data = curseforge_minecraft.get_data(mod, mc_version, 'Beta')

    if mod_data == None and release_phase == 'Beta':
        mod_data = curseforge_minecraft.get_data(mod, mc_version, 'Alpha')

    return mod_data

parser = argparse.ArgumentParser(description='Download or update Minecraft mods from CurseForge. Change the mods in mods.txt to the CurseForge project IDs of the mods you want. (The CurseForge project ID is the "example-id" part of https://minecraft.curseforge.com/projects/example-id.) The mods will be downloaded to the downloads folder.')
parser.add_argument('mc_version', help='Minecraft version to download mods for (supported: all versions between 1.7.2 and 1.12.2 that have Forge)')
parser.add_argument('release_phase', help='Least stable release phase to accept (supported: Release, Beta, Alpha)')
args = parser.parse_args()
print(args)

status = {}

if os.path.isfile('status.json'):
    with open('status.json') as status_json:
        status = json.loads(status_json.read())

if not os.path.isdir('downloads/'):
    os.mkdir('downloads/')

mods = open('mods.txt')

for mod in mods:
    mod = mod[:-1]
    print('Checking for {} update...'.format(mod))
    mod_data = get_mod_data(mod, args.mc_version, args.release_phase)
    print(mod_data)

    if mod_data == None and args.mc_version == '1.8.9':
        mod_data = get_mod_data(mod, '1.8.8', args.release_phase)

    if mod_data == None and args.mc_version == '1.10.2':
        mod_data = get_mod_data(mod, '1.10.0', args.release_phase)

    if mod_data == None and args.mc_version in ('1.10', '1.10.0', '1.10.2'):
        mod_data = get_mod_data(mod, '1.9.4', args.release_phase)

    if mod_data == None and args.mc_version == '1.11.2':
        mod_data = get_mod_data(mod, '1.11.0', args.release_phase)

    old_mod_time = -1

    try:
        old_mod_time = status[mod]
    except KeyError:
        pass

    if mod_data['time'] > old_mod_time:
        print('Found update! Downloading...')
        os.chdir('downloads/')
        subprocess.call(['wget', '--content-disposition', mod_data['url']])
        os.chdir('..')
        status[mod] = mod_data['time']
    else:
        print('No update found.')

json.dump(status, open('status.json', 'w'))
