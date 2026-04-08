HEADER_HTML = (
    '<table class="simpleTable">\n'
    "<tbody>\n"
    "<tr><th colspan=7><strong>Upstream Bonded Channels</strong></th></tr>\n"
    "      <td><strong>Channel</strong></td>\n"
    "      <td><strong>Channel ID</strong></td>\n"
    "      <td><strong>Lock Status</strong></td>\n"
    "      <td><strong>US Channel Type</td>\n"
    "      <td><strong>Frequency</strong></td>\n"
    "      <td><strong>Width</strong></td>\n"
    "      <td><strong>Power</strong></td>\n"
    "   </tr>\n"
)


def test__to_html__no_rows(upstream_bonded_channels_factory):
    channels = upstream_bonded_channels_factory.build(rows=[])

    html = channels.to_html()

    expected_html = HEADER_HTML + "\n</tbody>\n</table>"
    assert html == expected_html


def test__to_html(
    upstream_bonded_channels_factory,
    upstream_bonded_channels_row_factory,
):
    rows = upstream_bonded_channels_row_factory.batch(2)
    channels = upstream_bonded_channels_factory.build(rows=rows)

    html = channels.to_html()

    expected_html = (
        HEADER_HTML
        + rows[0].to_html()
        + "\n"
        + rows[1].to_html()
        + "\n</tbody>\n</table>"
    )
    assert html == expected_html
