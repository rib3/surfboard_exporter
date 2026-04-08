from testsupport.modem_html import UpstreamBondedChannels


def test__build(upstream_bonded_channels_factory):
    channels = upstream_bonded_channels_factory.build()

    assert isinstance(channels, UpstreamBondedChannels)
    assert isinstance(channels.rows, list)
    assert 0 <= len(channels.rows) <= 4


def test__build__rows__len(upstream_bonded_channels_factory):
    instances = upstream_bonded_channels_factory.batch(10)

    assert all(0 <= len(c.rows) <= 4 for c in instances)
