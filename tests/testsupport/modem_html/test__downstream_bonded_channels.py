HEADER_HTML = (
    '<table class="simpleTable">\n'
    "<tbody>\n"
    "<tr><th colspan=8><strong>Downstream Bonded Channels</strong></th></tr>\n"
    "      <td><strong>Channel ID</strong></td>\n"
    "      <td><strong>Lock Status</strong></td>\n"
    "      <td><strong>Modulation</strong></td>\n"
    "      <td><strong>Frequency</strong></td>\n"
    "      <td><strong>Power</strong></td>\n"
    "      <td><strong>SNR/MER</strong></td>\n"
    "      <td><strong>Corrected</strong></td>\n"
    "      <td><strong>Uncorrectables</strong></td>\n"
    "   </tr>\n"
)


def test__to_html__no_rows(downstream_bonded_channels_factory):
    channels = downstream_bonded_channels_factory.build(rows=[])

    html = channels.to_html()

    expected_html = HEADER_HTML + "\n</tbody>\n</table>"
    assert html == expected_html


def test__to_html(
    downstream_bonded_channels_factory,
    downstream_bonded_channels_row_factory,
):
    rows = downstream_bonded_channels_row_factory.batch(2)
    channels = downstream_bonded_channels_factory.build(rows=rows)

    html = channels.to_html()

    expected_html = (
        HEADER_HTML
        + rows[0].to_html()
        + "\n"
        + rows[1].to_html()
        + "\n</tbody>\n</table>"
    )
    assert html == expected_html
