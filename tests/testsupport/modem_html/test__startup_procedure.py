from testsupport.modem_html import StartupProcedure


def _expected_html(
    *,
    connectivity_state: str = "OK",
    connectivity_state_comment: str = "Operational",
    security: str = "Enabled",
    security_comment: str = "BPI+",
) -> str:
    return (
        '<table class="simpleTable">\n'
        "<tbody>\n"
        "<tr><th colspan=3><strong>Startup Procedure</strong></th></tr>\n"
        "<tr>\n"
        '      <td width="44%"><strong><u>Procedure</u></strong></td>\n'
        '      <td width="31%"><strong><u>Status</u></strong></td>\n'
        '      <td width="25%"><strong><u>Comment</u></strong></td>\n'
        "   </tr>\n"
        "   <tr>\n"
        "      <td>Acquire Downstream Channel</td>\n"
        "      <td>975000000 Hz</td>\n"
        "      <td>Locked</td>\n"
        "   </tr>\n"
        "   <tr>\n"
        "      <td>Connectivity State</td>\n"
        f"      <td>{connectivity_state}</td>\n"
        f"      <td>{connectivity_state_comment}</td>\n"
        "   </tr>\n"
        "   <tr>\n"
        "      <td>Boot State</td>\n"
        "      <td>OK</td>\n"
        "      <td>Operational</td>\n"
        "   </tr>\n"
        "   <tr>\n"
        "      <td>Configuration File</td>\n"
        "      <td>OK</td>\n"
        "      <td></td>\n"
        "   </tr>\n"
        "   <tr>\n"
        "      <td>Security</td>\n"
        f"      <td>{security}</td>\n"
        f"      <td>{security_comment}</td>\n"
        "   </tr>\n"
        "   <tr>\n"
        "      <td>DOCSIS Network Access Enabled</td>\n"
        "      <td>Allowed</td>\n"
        "      <td></td>\n"
        "   </tr>\n"
        "</tbody>\n"
        "</table>"
    )


def test__to_html__connectivity_state__ok():
    page = StartupProcedure(
        connectivity_state="OK",
        connectivity_state_comment="Operational",
        security="Enabled",
        security_comment="BPI+",
    )

    html = page.to_html()

    assert html == _expected_html(connectivity_state="OK")


def test__to_html__connectivity_state__not_synchronized():
    page = StartupProcedure(
        connectivity_state="Not Synchronized",
        connectivity_state_comment="Operational",
        security="Enabled",
        security_comment="BPI+",
    )

    html = page.to_html()

    assert html == _expected_html(connectivity_state="Not Synchronized")


def test__to_html__connectivity_state_comment__varied():
    page = StartupProcedure(
        connectivity_state="OK",
        connectivity_state_comment="BOGUS_TEST_COMMENT",
        security="Enabled",
        security_comment="BPI+",
    )

    html = page.to_html()

    assert html == _expected_html(connectivity_state_comment="BOGUS_TEST_COMMENT")


def test__to_html__security__disabled():
    page = StartupProcedure(
        connectivity_state="OK",
        connectivity_state_comment="Operational",
        security="Disabled",
        security_comment="BPI+",
    )

    html = page.to_html()

    assert html == _expected_html(security="Disabled")


def test__to_html__security_comment__varied():
    page = StartupProcedure(
        connectivity_state="OK",
        connectivity_state_comment="Operational",
        security="Enabled",
        security_comment="BOGUS_TEST_COMMENT",
    )

    html = page.to_html()

    assert html == _expected_html(security_comment="BOGUS_TEST_COMMENT")
