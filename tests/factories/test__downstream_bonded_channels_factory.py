from testsupport.modem_html import DownstreamBondedChannels


def test__build(downstream_bonded_channels_factory):
    channels = downstream_bonded_channels_factory.build()

    assert isinstance(channels, DownstreamBondedChannels)
    assert isinstance(channels.rows, list)
    assert len(channels.rows) in {0, 24, 25}


def test__build__rows__len(downstream_bonded_channels_factory):
    instances = downstream_bonded_channels_factory.batch(10)

    assert all(len(c.rows) in {0, 24, 25} for c in instances)
