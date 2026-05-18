from surfboard_exporter.parser import (
    ConnectivityState,
    DocsisNetworkAccess,
    DownstreamChannel,
    Security,
    UpstreamChannel,
)
from testsupport.modem_html import ConnectionStatus


def expected_system_time_get(connection_status: ConnectionStatus) -> float:
    system_time = connection_status.system_time
    if system_time is None:
        return float("nan")
    return system_time.timestamp()


def expected_connectivity_state_get(
    connection_status: ConnectionStatus,
) -> ConnectivityState:
    startup = connection_status.startup
    return ConnectivityState(
        ok=startup.connectivity_state == "OK",
        comment=startup.connectivity_state_comment,
    )


def expected_security_get(connection_status: ConnectionStatus) -> Security:
    startup = connection_status.startup
    return Security(
        enabled=startup.security == "Enabled",
        comment=startup.security_comment,
    )


def expected_docsis_network_access_get(
    connection_status: ConnectionStatus,
) -> DocsisNetworkAccess:
    startup = connection_status.startup
    return DocsisNetworkAccess(
        allowed=startup.docsis_network_access_enabled == "Allowed",
        comment=startup.docsis_network_access_enabled_comment,
    )


def expected_downstream_channels_get(
    connection_status: ConnectionStatus,
) -> list[DownstreamChannel]:
    return [
        DownstreamChannel(
            channel_id=row.channel_id,
            lock_status=row.lock_status,
            modulation=row.modulation,
            frequency_hz=row.frequency_hz,
            power_dbmv=row.power_dbmv,
            snr_db=row.snr_db,
            corrected=row.corrected,
            uncorrectables=row.uncorrectables,
        )
        for row in connection_status.downstream.rows
    ]


def expected_upstream_channels_get(
    connection_status: ConnectionStatus,
) -> list[UpstreamChannel]:
    return [
        UpstreamChannel(
            channel_id=row.channel_id,
            lock_status=row.lock_status,
            channel_type=row.channel_type,
            frequency_hz=row.frequency_hz,
            width_hz=row.width_hz,
            power_dbmv=row.power_dbmv,
        )
        for row in connection_status.upstream.rows
    ]
