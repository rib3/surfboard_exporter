from testsupport.modem_html import DownstreamBondedChannelsRow


def test__build(downstream_bonded_channels_row_factory):
    row = downstream_bonded_channels_row_factory.build()

    assert isinstance(row, DownstreamBondedChannelsRow)
    assert isinstance(row.channel_id, int)
    assert isinstance(row.lock_status, str)
    assert isinstance(row.modulation, str)
    assert isinstance(row.frequency_hz, int)
    assert isinstance(row.power_dbmv, float)
    assert isinstance(row.snr_db, float)
    assert isinstance(row.corrected, int)
    assert isinstance(row.uncorrectables, int)
