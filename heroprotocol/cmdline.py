#!/usr/bin/env python
#
# Copyright (c) 2015 Blizzard Entertainment
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import argparse
import pprint
import json

from mpyq import MPQArchive

from .protocols import protocol29406

from .heroprotocol import HeroProtocol


class EventLogger:
    def __init__(self):
        self._event_stats = {}

    def log(self, output, event):
        # update stats
        if '_event' in event and '_bits' in event:
            stat = self._event_stats.get(event['_event'], [0, 0])
            stat[0] += 1  # count of events
            stat[1] += event['_bits']  # count of bits
            self._event_stats[event['_event']] = stat
        # write structure
        if args.json:
            s = json.dumps(event, encoding="ISO-8859-1");
            print(s);
        else:
            pprint.pprint(event, stream=output)

    def log_stats(self, output):
        for name, stat in sorted(self._event_stats.iteritems(), key=lambda x: x[1][1]):
            print >> output, '"%s", %d, %d,' % (name, stat[0], stat[1] / 8)


def main():
    """Main entry point from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument('replay_file', help='.StormReplay file to load')
    parser.add_argument("--gameevents", help="print game events",
                        action="store_true")
    parser.add_argument("--messageevents", help="print message events",
                        action="store_true")
    parser.add_argument("--trackerevents", help="print tracker events",
                        action="store_true")
    parser.add_argument("--attributeevents", help="print attributes events",
                        action="store_true")
    parser.add_argument("--header", help="print protocol header",
                        action="store_true")
    parser.add_argument("--details", help="print protocol details",
                        action="store_true")
    parser.add_argument("--initdata", help="print protocol initdata",
                        action="store_true")
    parser.add_argument("--stats", help="print stats",
                        action="store_true")
    parser.add_argument("--json", help="protocol information is printed in json format.",
                        action="store_true")
    args = parser.parse_args()

    hero_protocol = HeroProtocol(args.replay_file)

    logger = EventLogger()
    logger.args = args;

    if args.header:
        logger.log(sys.stdout, hero_protocol.decode_header())
        
    if args.details:
        logger.log(sys.stdout, hero_protocol.decode_replay_details())

    if args.initdata:
        initdata = hero_protocol.decode_replay_initdata()
        logger.log(sys.stdout, initdata['m_syncLobbyState']['m_gameDescription']['m_cacheHandles'])
        logger.log(sys.stdout, initdata)

    if args.gameevents:
        for event in hero_protocol.decode_replay_game_events():
            logger.log(sys.stdout, event)

    if args.messageevents:
        for event in hero_protocol.decode_replay_message_events():
            logger.log(sys.stdout, event)

    if args.trackerevents:
        for event in hero_protocol.decode_replay_tracker_events():
            logger.log(sys.stdout, event)

    if args.attributeevents:
        logger.log(sys.stdout, hero_protocol.decode_replay_attributes_events())
        
    if args.stats:
        logger.log_stats(sys.stderr)
