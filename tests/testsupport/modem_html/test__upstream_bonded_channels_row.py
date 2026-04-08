from testsupport.modem_html import UpstreamBondedChannelsRow


def test__to_html__static():
    row = UpstreamBondedChannelsRow(
        channel=1,
        channel_id=1,
        lock_status="Locked",
        channel_type="ATDMA",
        frequency_hz=38596000,
        width_hz=6400000,
        power_dbmv=46.0,
    )

    html = row.to_html()

    expected_html = (
        "   <tr align='left'>\n"
        "      <td>1</td>\n"
        "      <td>1</td>\n"
        "      <td>Locked</td>\n"
        "      <td>ATDMA</td>\n"
        "      <td>38596000 Hz</td>\n"
        "      <td>6400000 Hz</td>\n"
        "      <td>46.0 dBmV</td>\n"
        "   </tr>"
    )
    assert html == expected_html


def test__to_html(upstream_bonded_channels_row_factory):
    row = upstream_bonded_channels_row_factory.build()

    html = row.to_html()

    expected_html = (
        "   <tr align='left'>\n"
        f"      <td>{row.channel}</td>\n"
        f"      <td>{row.channel_id}</td>\n"
        f"      <td>{row.lock_status}</td>\n"
        f"      <td>{row.channel_type}</td>\n"
        f"      <td>{row.frequency_hz} Hz</td>\n"
        f"      <td>{row.width_hz} Hz</td>\n"
        f"      <td>{row.power_dbmv} dBmV</td>\n"
        "   </tr>"
    )
    assert html == expected_html
