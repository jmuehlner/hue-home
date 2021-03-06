#!/usr/bin/python

from phue import Bridge

import argparse
import logging
import sys

logging.basicConfig()

LOGGER = logging.getLogger(__name__)

def hue_state_parser(value):

    # First check if it's simply on or off
    value = value.lower()
    if value == 'on' or value == 'off':
        return value

    # Check if it's a valid number
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid state: "{}".'.format(value))

    # At this point, it must be a valid integer
    if value > 254 or value < 1:
        raise argparse.ArgumentTypeError('Brightness must be < 255 and > 0.')

    return value


parser = argparse.ArgumentParser(description='Hue Control.')
parser.add_argument('state', type=hue_state_parser,
                    help='The state to set the light(s) to - may be on/off or a brightness from 1 to 254.')
parser.add_argument('-l', action='append', help='A light to apply the new state to. Can be specified multiple times.')
parser.add_argument('-r', action='append', help='A room to apply the new state to. Can be specified multiple times.')
parser.add_argument('-t', type=int, help='Transition time, in seconds.')
args = parser.parse_args()

state = args.state
lights = args.l
rooms = args.r
transition = args.t

# 'Philips-hue` is the hostname. IP Could work too
bridge = Bridge('Philips-hue')

# Turn lights on
if state == 'on':
    action = {'on': True}

# Turn lights off
elif state == 'off':
    action = {'on': False}

# Brightness numeric value - note that the light must always be turned on before adjusting brightness
else:
    action = {'on': True, 'bri': state}

# Add the transition time, if any
if transition:
    action['transitiontime'] = transition

# Prefetch all bridge state
bridge_data = bridge.get_api()
all_lights = set(light['name'] for light in bridge_data['lights'].values())

# Apply the state to all the lights on the bridge if none are specified
if lights is None and rooms is None:
    bridge.set_light(all_lights, action)
    sys.exit(0)

# Just set the lights
if lights:
    lights = set(lights)

    invalid_lights = lights.difference(all_lights)
    if invalid_lights:
        LOGGER.error('{} are invalid. Valid lights: {}.'.format(list(invalid_lights), list(all_lights)))
        sys.exit(1)

    bridge.set_light(lights, action)

# Apply state to all lights in the rooms
if rooms:
    rooms = set(rooms)

    all_rooms = {group['name']: group for group in bridge_data['groups'].values() if group['type'] == 'Room'}

    invalid_rooms = set(rooms).difference(all_rooms.keys())
    if invalid_rooms:
        LOGGER.error('{} are invalid. Valid rooms: {}.'.format(list(invalid_rooms), list(all_rooms)))
        sys.exit(1)

    # Get all light IDs from all specified rooms
    light_ids = []
    for room in [all_rooms[room] for room in rooms]:
        light_ids.extend(room['lights'])

    # Determine the names of the lights
    lights = [bridge_data['lights'][id]['name'] for id in light_ids]

    bridge.set_light(lights, action)
