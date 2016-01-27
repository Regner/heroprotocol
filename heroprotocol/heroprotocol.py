

from mpyq import MPQArchive
from importlib import import_module

from .protocols import protocol29406
from .exceptions import ProtocolNotFound

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
            contents = self._archive.header['user_data_header']['content']

            # It doesn't matter which protocol we use to load the headers
            header = protocol29406.decode_replay_header(contents)
            baseBuild = header['m_version']['m_baseBuild']

            try:
                self._protocol = import_module('heroprotocol.protocols.protocol{}'.format(baseBuild))

            except NameError:
                raise ProtocolNotFound('Protocol not found for base: {}'.format(baseBuild))

        return self._protocol

    def decode_header(self):
        """Header for the replay file.

        Returns:
            dict


        """
        contents = self._archive.header['user_data_header']['content']
        return self.protocol.decode_replay_header(contents)


    def decode_replay_details(self):
        """A basic overview of a replays details.

        This includes higher level things such as the player list, the player's
        heroes, the map name, and more.

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.details')
        return self.protocol.decode_replay_details(contents)

    def decode_replay_initdata(self):
        """

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.initData')
        return self.protocol.decode_replay_initdata(contents)

    def decode_replay_game_events(self):
        """

        Returns:
            generator

        """
        contents = self._archive.read_file('replay.game.events')
        yield self.protocol.decode_replay_game_events(contents)

    def decode_replay_message_events(self):
        """

        Returns:
            generator

        """
        contents = self._archive.read_file('replay.message.events')
        yield self.protocol.decode_replay_message_events(contents)

    def decode_replay_tracker_events(self):
        """

        Returns:
            generator

        """
        contents = self._archive.read_file('replay.tracker.events')

        # We possibly want to raise an error here? Not sure, the current command
        # line interface would just silently skip this if the attr wasn't there.
        # This implementation provides the same results. Not sure the use case
        # of this so not sure the best thing to do.
        if hasattr(self.protocol, 'decode_replay_tracker_eventssss'):
            yield self.protocol.decode_replay_tracker_events(contents)

        else:
            yield

    def decode_replay_attributes_events(self):
        """

        Returns:
            dict

        """
        contents = self._archive.read_file('replay.attributes.events')
        return self.protocol.decode_replay_attributes_events(contents)
