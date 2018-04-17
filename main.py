#!/usr/bin/python3

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
import urllib.request

from download_helper.downloaders import curseforge

SRG_COMPAT_MAP = {
    '1.8.9': ['1.8.8'],
    '1.10': ['1.9.4'],
    '1.10.2': ['1.10', '1.9.4'],
    '1.11.2': ['1.11'],
    '1.12.1': ['1.12'],
    '1.12.2': ['1.12.1', '1.12'],
}


def upgrade_status():
    global status

    if status['version'] == 1:
        del status['version']
        status_old = status

        status = {
            'version': 2,
            'mods': {},
        }

        for mod in status_old:
            status['mods'][curseforge.addon_slug_to_id('mc', mod)] = {
                'time': status_old[mod],
                'explicit': True,
            }


def process_mod(addon_id, explicit=True):
    addon_data = curseforge.get_data(addon_id, args.mc_version, args.release_type,
                                     extra_game_versions=extra_minecraft_versions,
                                     allow_less_stable_release_types=args.allow_less_stable_release_types)
    old_mod_time = -1

    try:
        old_mod_time = status['mods'][addon_id]['time']
    except KeyError:
        pass

    for dependency in addon_data['extra']['dependencies']:
        if dependency['Type'] == 'Required':
            pending_dependencies.append(dependency['AddOnId'])

    if addon_data['time'] > old_mod_time:
        urllib.request.urlretrieve(addon_data['url'],
                                   os.path.abspath(os.path.join('downloads/', addon_data['file_name'])))

        if addon_id not in status['mods']:
            status['mods'][addon_id] = {
                'explicit': explicit
            }

        status['mods'][addon_id]['time'] = addon_data['time']

    return addon_data


parser = argparse.ArgumentParser(
    description='Download or update Minecraft mods from CurseForge. Change the mods in mods.txt to the CurseForge addon slugs of the mods you want. (The CurseForge addon slug is the "example-id" part of https://minecraft.curseforge.com/projects/example-id.) The mods will be downloaded to the downloads folder.')
parser.add_argument('mc_version', help='Minecraft version to download mods for')
parser.add_argument('release_type', help='Least stable release type to accept (supported: Release, Beta, Alpha)')
parser.add_argument('--allow-less-stable-release-types', action='store_true',
                    help='Allow less stable release types if a mod is not available with the specified release type. (default: false)')
args = parser.parse_args()

status = {
    'version': 2,
    'mods': {},
}

if os.path.isfile('status.json'):
    with open('status.json') as status_json:
        status = json.loads(status_json.read())

if 'version' not in status:
    status['version'] = 1

if not os.path.isdir('downloads/'):
    os.mkdir('downloads/')

print('Preparing...')
upgrade_status()
extra_minecraft_versions = SRG_COMPAT_MAP[args.mc_version] if args.mc_version in SRG_COMPAT_MAP else []
mods = [curseforge.addon_slug_to_id('mc', mod.strip()) for mod in open('mods.txt')]
pending_dependencies = []

for mod in status['mods']:
    if status['mods'][mod]['explicit'] and mod not in mods:
        del status['mods'][mod]

print('Updating mods...')
for mod in mods:
    process_mod(mod)

print('Resolving and updating dependencies...')
processed_dependencies = []

while pending_dependencies:
    pending_dependencies = list(set(pending_dependencies))
    dependencies_to_process = pending_dependencies

    for dependency in dependencies_to_process:
        pending_dependencies.remove(dependency)

        if (not (dependency in status['mods'] and status['mods'][dependency][
            'explicit'])) and dependency not in processed_dependencies:
            new_dependency = dependency not in status['mods']
            addon_data = process_mod(dependency, explicit=False)

            if new_dependency:
                print('New dependency: {}'.format(addon_data['file_name']))

            processed_dependencies.append(dependency)

print('Looking for orphaned dependencies...')
for mod in status['mods']:
    if (not status['mods'][mod]['explicit']) and mod not in processed_dependencies:
        print('Orphaned dependency: {}'.format(curseforge.get_addon_name(mod)))
        del status['mods'][mod]

json.dump(status, open('status.json', 'w'))
