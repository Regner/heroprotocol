

from mpyq import MPQArchive
from importlib import import_module

from .protocols import protocol29406
from .exceptions import ProtocolNotFound
from .decoders import BitPackedBuffer, BitPackedDecoder, VersionedDecoder


class HeroProtocol(object):
    """Provides a wraper around the protocol interface.

    Examples:
        >>> from pprint import pprint
        >>> from heroprotocol import HeroProtocol
        >>> hero_protocol = HeroProtocol('Awesome Replay.StormReplay')
        >>> pprint(hero_protocol.decode_header())
        {'m_dataBuildNum': 39271,
         'm_elapsedGameLoops': 23783,
         'm_fixedFileHash': {'m_data': 'IV\x9aO\xe7I\x10\x8fS\xc4\xbf\x894}.\x0c'},
         'm_ngdpRootKey': {'m_data': 'O\x84\xdd\t\xb2\xbb\x96\xd1\xd8Z5W\xbf\x84\xbd\x0c'},
         'm_signature': 'Heroes of the Storm replay\x1b11',
         'm_type': 2,
         'm_useScaledTime': False,
         'm_version': {'m_baseBuild': 39271,
                       'm_build': 39271,
                       'm_flags': 1,
                       'm_major': 0,
                       'm_minor': 15,
                       'm_revision': 1}}

    """

    def __init__(self, replay_path):
        """

        Args:
            replay_path (str): Path to the .StormReplay file to be parsed.

        """
        self._replay_path = replay_path
        self._archive = MPQArchive(replay_path)

    def __repr__(self):
        return '<HeroProtocol: {}>'.format(self._replay_path)

    @property
    def protocol(self):
        """The protocol for decoding a replay file based on the replays version.

        When called for the first time it will cache the chosen protocol.
        Because of this behaviour it is important that self._archive does not
        change during runtime. Basically don't try and reuse the same
        HeroProtocol instance for multiple replay files.

        Returns:
            protocol: 

        Raises:
            ProtocolNotFound: If a protocol cannot be found that matches the
                base build for the supplied replay file.

        """
        try:
            return self._protocol

        except AttributeError:
            # It doesn't matter which protocol we use to load the headers
            contents = self._archive.header['user_data_header']['content']
            decoder = VersionedDecoder(contents, protocol29406.typeinfos)
            header = decoder.instance(protocol29406.replay_header_typeid)
            base_build = header['m_version']['m_baseBuild']

            try:
                self._protocol = import_module('heroprotocol.protocols.protocol{}'.format(base_build))

            except NameError:
                raise ProtocolNotFound('Protocol not found for base: {}'.format(base_build))

        return self._protocol

    def decode_header(self):
        """Decodes and return the replay header from the contents byte string.

        Returns:
            dict


        """
        contents = self._archive.header['user_data_header']['content']
        decoder = VersionedDecoder(contents, self.protocol.typeinfos)
        return decoder.instance(self.protocol.replay_header_typeid)

    def decode_replay_details(self):
        """Decodes and returns the game details from the contents byte string.

        This includes higher level things such as the player list, the player's
        heroes, the map name, and more.

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.details')
        decoder = VersionedDecoder(contents, self.protocol.typeinfos)
        return decoder.instance(self.protocol.game_details_typeid)

    def decode_replay_initdata(self):
        """Decodes and return the replay init data from the contents byte string.

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.initData')
        decoder = BitPackedDecoder(contents, self.protocol.typeinfos)
        return decoder.instance(self.protocol.replay_initdata_typeid)

    def decode_replay_game_events(self):
        """Decodes and yields each game event from the contents byte string.

        Returns:
            generator

        """
        contents = self._archive.read_file('replay.game.events')
        decoder = BitPackedDecoder(contents, self.protocol.typeinfos)
        events = self._decode_event_stream(
            decoder,
            self.protocol.game_eventid_typeid,
            self.protocol.game_event_types,
            decode_user_id=True
        )

        for event in events:
            yield event

    def decode_replay_message_events(self):
        """Decodes and yields each message event from the contents byte string.

        Returns:
            generator

        """

        contents = self._archive.read_file('replay.message.events')
        decoder = BitPackedDecoder(contents, self.protocol.typeinfos)
        events = self._decode_event_stream(
            decoder,
            self.protocol.message_eventid_typeid,
            self.protocol.message_event_types,
            decode_user_id=True
        )

        for event in events:
            yield event

    def decode_replay_tracker_events(self):
        """Decodes and yields each tracker event from the contents byte string.

        Returns:
            generator



        We possibly want to raise an error here? Not sure, the current command
        line interface would just silently skip this if the attr wasn't there.
        This implementation provides the same results. Not sure the use case
        of this so not sure the best thing to do.
        if hasattr(self.protocol, 'decode_replay_tracker_eventssss'):
            yield self.protocol.decode_replay_tracker_events(contents)

        else:
            yield

        """
        contents = self._archive.read_file('replay.tracker.events')
        decoder = VersionedDecoder(contents, self.protocol.typeinfos)
        events = self._decode_event_stream(
            decoder,
            self.protocol.tracker_eventid_typeid,
            self.protocol.tracker_event_types,
            decode_user_id=False
        )

        for event in events:
            yield event

    def decode_replay_attributes_events(self):
        """Decodes and yields each attribute from the contents byte string.

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.attributes.events')
        bit_buffer = BitPackedBuffer(contents, 'little')
        attributes = {}

        if not bit_buffer.done():
            attributes['source'] = bit_buffer.read_bits(8)
            attributes['mapNamespace'] = bit_buffer.read_bits(32)
            attributes['scopes'] = {}
            bit_buffer.read_bits(32)

            while not bit_buffer.done():
                value = dict()
                value['namespace'] = bit_buffer.read_bits(32)
                value['attrid'] = attrid = bit_buffer.read_bits(32)
                scope = bit_buffer.read_bits(8)
                value['value'] = bit_buffer.read_aligned_bytes(4)[::-1].strip('\x00')
                if scope not in attributes['scopes']:
                    attributes['scopes'][scope] = {}
                if attrid not in attributes['scopes'][scope]:
                    attributes['scopes'][scope][attrid] = []
                attributes['scopes'][scope][attrid].append(value)
        return attributes

    def _decode_event_stream(self, decoder, eventid_typeid, event_types, decode_user_id):
        """Decodes events prefixed with a gameloop and possibly userid."""
        gameloop = 0
        while not decoder.done():
            start_bits = decoder.used_bits()

            # decode the gameloop delta before each event
            delta = self._varuint32_value(decoder.instance(self.protocol.svaruint32_typeid))
            gameloop += delta

            # decode the userid before each event
            if decode_user_id:
                userid = decoder.instance(self.protocol.replay_userid_typeid)

            # decode the event id
            eventid = decoder.instance(eventid_typeid)
            typeid, typename = event_types.get(eventid, (None, None))
            if typeid is None:
                raise CorruptedError('eventid(%d) at %s' % (eventid, decoder))

            # decode the event struct instance
            event = decoder.instance(typeid)
            event['_event'] = typename
            event['_eventid'] = eventid

            #  insert gameloop and userid
            event['_gameloop'] = gameloop
            if decode_user_id:
                event['_userid'] = userid

            # the next event is byte aligned
            decoder.byte_align()

            # insert bits used in stream
            event['_bits'] = decoder.used_bits() - start_bits

            yield event

    @staticmethod
    def _varuint32_value(value):
        """Returns the numeric value from a SVarUint32 instance."""
        for k, v in value.iteritems():
            return v
        return 0

    @staticmethod
    def unit_tag(unit_tag_index, unit_tag_recycle):
        return (unit_tag_index << 18) + unit_tag_recycle

    @staticmethod
    def unit_tag_index(unit_tag):
        return (unit_tag >> 18) & 0x00003fff

    @staticmethod
    def unit_tag_recycle(unit_tag):
        return (unit_tag) & 0x0003ffff
