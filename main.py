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
import argparse
import json
import os
import subprocess

from download_helper.downloaders import curseforge

SRG_COMPAT_MAP = {
    '1.8.9': ['1.8.8'],
    '1.10': ['1.9.4'],
    '1.10.2': ['1.10', '1.9.4'],
    '1.11.2': ['1.11'],
    '1.12.1': ['1.12'],
    '1.12.2': ['1.12.1', '1.12'],
}

parser = argparse.ArgumentParser(
    description='Download or update Minecraft mods from CurseForge. Change the mods in mods.txt to the CurseForge addon slugs of the mods you want. (The CurseForge addon slug is the "example-id" part of https://minecraft.curseforge.com/projects/example-id.) The mods will be downloaded to the downloads folder.')
parser.add_argument('mc_version', help='Minecraft version to download mods for')
parser.add_argument('release_type', help='Least stable release type to accept (supported: Release, Beta, Alpha)')
args = parser.parse_args()

status = {}

if os.path.isfile('status.json'):
    with open('status.json') as status_json:
        status = json.loads(status_json.read())

if not os.path.isdir('downloads/'):
    os.mkdir('downloads/')

extra_minecraft_versions = SRG_COMPAT_MAP[args.mc_version] if args.mc_version in SRG_COMPAT_MAP else []
mods = open('mods.txt')

for mod in mods:
    mod = mod[:-1]
    print('Checking for {} update...'.format(mod))
    addon_id = curseforge.addon_slug_to_id('mc', mod)
    mod_data = curseforge.get_data(addon_id, args.mc_version, args.release_type,
                                   extra_game_versions=extra_minecraft_versions)
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
