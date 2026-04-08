from testsupport.modem_html import UpstreamBondedChannelsRow


def test__build(upstream_bonded_channels_row_factory):
    row = upstream_bonded_channels_row_factory.build()

    assert isinstance(row, UpstreamBondedChannelsRow)
    assert isinstance(row.channel, int)
    assert isinstance(row.channel_id, int)
    assert isinstance(row.lock_status, str)
    assert isinstance(row.channel_type, str)
    assert isinstance(row.frequency_hz, int)
    assert isinstance(row.width_hz, int)
    assert isinstance(row.power_dbmv, float)
