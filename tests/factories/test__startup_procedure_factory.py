from testsupport.modem_html import StartupProcedure


def test__build(startup_procedure_factory):
    page = startup_procedure_factory.build()

    assert isinstance(page, StartupProcedure)
    assert isinstance(page.connectivity_state, str)
    assert isinstance(page.connectivity_state_comment, str)
    assert isinstance(page.security, str)
    assert isinstance(page.security_comment, str)
