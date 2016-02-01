

import os
import pytest

from heroprotocol import HeroProtocol


def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for version in metafunc.cls.versions:
        idlist.append(version)
        argnames = ['version']
        argvalues.append(([version]))
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


def get_test_versions():
    versions = []
    version_path_formatter = 'tests/replays/{}'

    for replay in os.listdir('tests/replays/'):
        versions.append(version_path_formatter.format(replay))

    return versions


class TestHeroProtocolAllVersions:
    versions = get_test_versions()

    def test_repre(self, version):
        hp = HeroProtocol(version)
        assert hp.__repr__() == '<HeroProtocol: {}>'.format(version)

    def test_decode_header(self, version):
        hp = HeroProtocol(version)
        hp.decode_header()

    def test_decode_replay_details(self, version):
        hp = HeroProtocol(version)
        hp.decode_replay_details()

    def test_decode_replay_initdata(self, version):
        hp = HeroProtocol(version)
        hp.decode_replay_initdata()

    def test_decode_replay_game_events(self, version):
        hp = HeroProtocol(version)
        for x in hp.decode_replay_game_events():
            pass

    def test_decode_replay_message_events(self, version):
        hp = HeroProtocol(version)
        for x in hp.decode_replay_message_events():
            pass

    def test_decode_replay_tracker_events(self, version):
        hp = HeroProtocol(version)
        for x in hp.decode_replay_tracker_events():
            pass

    def test_decode_replay_attributes_events(self, version):
        hp = HeroProtocol(version)
        hp.decode_replay_attributes_events()
