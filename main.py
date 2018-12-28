#
# Copyright 2018-2019 by Satanowski
#

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Copyright (C) 2018-2019 Satanowski <satanowski@gmail.com>
License: GNU AGPLv3
"""

import pathlib
import logging
import sys
from subprocess import Popen, DEVNULL

import mido
import yaml
import click


# logging.basicConfig(level=logging.DEBUG)

class MidiAuto:
    """Lorem ipsum."""

    def __init__(self, profile='general'):
        self.config = {}
        self.midi_device = None
        self.load_conf()
        self.profile = self.config.get('profiles', {}).get(profile)
        if not self.profile:
            sys.exit('No profile defined ({})!'.format(profile))
        self.actions = self.config.get('actions', {})
        if not self.actions:
            sys.exit('No actions defined!')

        self.load_midi()

    def load_conf(self):
        """Load configuration."""
        config_file = pathlib.Path.home() / '.pymidautorc'
        if config_file.exists():
            with config_file.open() as cfg:
                self.config = yaml.load(cfg)
        else:
            sys.exit('No config file!')

    def load_midi(self):
        """Open input MIDI device."""
        midi_dev_name = self.config.get('midi_device')
        if not midi_dev_name:
            logging.error('No midi device configured!')
            sys.exit(1)
        self.midi_device = mido.open_input(midi_dev_name)  # pylint: disable=no-member

    @staticmethod
    def discovery():
        """List all MIDI devices."""
        for dev in mido.get_input_names():  # pylint: disable=no-member
            print(dev)

    @staticmethod
    def describe_midi_msg(msg):
        """Display MIDI event in nicer way."""
        typ = msg.type == 'control_change'
        txt = '\r{} {{}}: value: {{}}'.format('Controller' if typ else 'Note')
        val = (msg.control, msg.value) if typ else (msg.note, msg.velocity)
        sys.stdout.write('\r' + 79 * ' ')
        sys.stdout.write(txt.format(*val))

    def debug_midi(self):
        """Special mode for exploring device buttons :)."""
        try:
            print('Waiting for MIDI events...')
            while True:
                self.describe_midi_msg(self.midi_device.receive())
        except KeyboardInterrupt:
            sys.exit()


    def watch_and_react(self):
        """Wait for MIDI messages and run mapped actions (if any)."""
        controllers = self.profile.get('encoders')
        notes = self.profile.get('buttons')

        while True:
            msg = self.midi_device.receive()
            typ = msg.type == 'control_change'

            assignment = controllers.get(msg.control) if typ else notes.get(msg.note)
            if not assignment:
                continue

            if typ:
                action = self.actions.get(assignment['action'])
            else:
                action = self.actions.get(
                    assignment['up_action' if msg.velocity == 0 else 'down_action']
                )

            if not action:
                continue

            if action['type'] == 'shell':
                cmd = action['cmd']
                cmd = cmd.format(round(msg.value * 100 / 127)) if typ else cmd
                Popen(cmd.split(), stdout=DEVNULL, stderr=DEVNULL)
            else:
                # to do in the future
                pass


@click.command()
@click.option('--discover', default=False, is_flag=True,
              help="Try to find connected midi devices")
@click.option('--debug', default=False, is_flag=True,
              help="Watch events from configured midi device")
@click.option('--profile', default='general')
def main(profile=None, discover=False, debug=False):
    """Parse arguments and run..."""

    if discover:
        MidiAuto.discovery()
        sys.exit()

    midia = MidiAuto(profile)
    if debug:
        midia.debug_midi()
    midia.watch_and_react()


if __name__ == '__main__':
    main()
