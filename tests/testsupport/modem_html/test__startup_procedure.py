import pytest

from testsupport.modem_html import StartupProcedure

MISSING = object()


def _resolve_value(value, obj, attr: str, default):
    if value is not MISSING:
        return value
    if obj is not None:
        return getattr(obj, attr)
    return default


def _resolve_with(obj):
    def resolve(value, attr, default):
        return _resolve_value(value, obj, attr, default)

    return resolve


def _expected_html(
    startup_procedure: StartupProcedure | None = None,
    *,
    connectivity_state=MISSING,
    connectivity_state_comment=MISSING,
    security=MISSING,
    security_comment=MISSING,
) -> str:
    resolve = _resolve_with(startup_procedure)
    connectivity_state = resolve(connectivity_state, "connectivity_state", "OK")
    connectivity_state_comment = resolve(
        connectivity_state_comment, "connectivity_state_comment", "Operational"
    )
    security = resolve(security, "security", "Enabled")
    security_comment = resolve(security_comment, "security_comment", "BPI+")
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


def test__to_html__factory(startup_procedure_factory):
    startup = startup_procedure_factory.build()

    html = startup.to_html()

    assert html == _expected_html(startup)


@pytest.mark.parametrize(
    "attrs",
    [
        dict(connectivity_state="OK"),
        dict(connectivity_state="Not Synchronized"),
        dict(connectivity_state_comment="BOGUS_TEST_COMMENT"),
        dict(security="Disabled"),
        dict(security_comment="BOGUS_TEST_COMMENT"),
    ],
    ids=repr,
)
def test__to_html__attr(attrs, startup_procedure_factory):
    startup = startup_procedure_factory.build(**attrs)

    html = startup.to_html()

    assert html == _expected_html(startup, **attrs)
    assert html == _expected_html(startup)
