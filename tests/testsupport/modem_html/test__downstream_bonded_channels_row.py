from testsupport.modem_html import DownstreamBondedChannelsRow


def test__to_html__static():
    row = DownstreamBondedChannelsRow(
        channel_id=1,
        lock_status="Locked",
        modulation="QAM256",
        frequency_hz=387000000,
        power_dbmv=-8.2,
        snr_db=43.5,
        corrected=100,
        uncorrectables=0,
    )

    html = row.to_html()

    expected_html = (
        "   <tr align='left'>\n"
        "      <td>1</td>\n"
        "      <td>Locked</td>\n"
        "      <td>QAM256</td>\n"
        "      <td>387000000 Hz</td>\n"
        "      <td>-8.2 dBmV</td>\n"
        "      <td>43.5 dB</td>\n"
        "      <td>100</td>\n"
        "      <td>0</td>\n"
        "   </tr>"
    )
    assert html == expected_html


def test__to_html(downstream_bonded_channels_row_factory):
    row = downstream_bonded_channels_row_factory.build()

    html = row.to_html()

    expected_html = (
        "   <tr align='left'>\n"
        f"      <td>{row.channel_id}</td>\n"
        f"      <td>{row.lock_status}</td>\n"
        f"      <td>{row.modulation}</td>\n"
        f"      <td>{row.frequency_hz} Hz</td>\n"
        f"      <td>{row.power_dbmv} dBmV</td>\n"
        f"      <td>{row.snr_db} dB</td>\n"
        f"      <td>{row.corrected}</td>\n"
        f"      <td>{row.uncorrectables}</td>\n"
        "   </tr>"
    )
    assert html == expected_html
