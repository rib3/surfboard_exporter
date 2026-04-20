from dataclasses import dataclass, field
from datetime import datetime

STARTUP_PROCEDURE__TABLE_BEGIN = '<table class="simpleTable">\n<tbody>'
STARTUP_PROCEDURE__TITLE_ROW = (
    "<tr><th colspan=3><strong>Startup Procedure</strong></th></tr>"
)
STARTUP_PROCEDURE__COLUMN_HEADERS_ROW = (
    "<tr>\n"
    '      <td width="44%"><strong><u>Procedure</u></strong></td>\n'
    '      <td width="31%"><strong><u>Status</u></strong></td>\n'
    '      <td width="25%"><strong><u>Comment</u></strong></td>\n'
    "   </tr>"
)
STARTUP_PROCEDURE__TABLE_END = "</tbody>\n</table>"
STARTUP_PROCEDURE__BEGIN_TITLE_HEADERS = (
    f"{STARTUP_PROCEDURE__TABLE_BEGIN}\n"
    f"{STARTUP_PROCEDURE__TITLE_ROW}\n"
    f"{STARTUP_PROCEDURE__COLUMN_HEADERS_ROW}"
)

DOWNSTREAM__TABLE_BEGIN = '<table class="simpleTable">\n<tbody>'
DOWNSTREAM__TITLE_ROW = (
    "<tr><th colspan=8><strong>Downstream Bonded Channels</strong></th></tr>"
)
DOWNSTREAM__COLUMN_HEADERS_ROW = (
    "      <td><strong>Channel ID</strong></td>\n"
    "      <td><strong>Lock Status</strong></td>\n"
    "      <td><strong>Modulation</strong></td>\n"
    "      <td><strong>Frequency</strong></td>\n"
    "      <td><strong>Power</strong></td>\n"
    "      <td><strong>SNR/MER</strong></td>\n"
    "      <td><strong>Corrected</strong></td>\n"
    "      <td><strong>Uncorrectables</strong></td>\n"
    "   </tr>"
)
DOWNSTREAM__TABLE_END = "</tbody>\n</table>"
DOWNSTREAM__BEGIN_TITLE_HEADERS = (
    f"{DOWNSTREAM__TABLE_BEGIN}\n"
    f"{DOWNSTREAM__TITLE_ROW}\n"
    f"{DOWNSTREAM__COLUMN_HEADERS_ROW}"
)

UPSTREAM__TABLE_BEGIN = '<table class="simpleTable">\n<tbody>'
UPSTREAM__TITLE_ROW = (
    "<tr><th colspan=7><strong>Upstream Bonded Channels</strong></th></tr>"
)
UPSTREAM__COLUMN_HEADERS_ROW = (
    "      <td><strong>Channel</strong></td>\n"
    "      <td><strong>Channel ID</strong></td>\n"
    "      <td><strong>Lock Status</strong></td>\n"
    "      <td><strong>US Channel Type</td>\n"
    "      <td><strong>Frequency</strong></td>\n"
    "      <td><strong>Width</strong></td>\n"
    "      <td><strong>Power</strong></td>\n"
    "   </tr>"
)
UPSTREAM__TABLE_END = "</tbody>\n</table>"
UPSTREAM__BEGIN_TITLE_HEADERS = (
    f"{UPSTREAM__TABLE_BEGIN}\n"
    f"{UPSTREAM__TITLE_ROW}\n"
    f"{UPSTREAM__COLUMN_HEADERS_ROW}"
)


@dataclass
class StartupProcedure:
    connectivity_state: str
    connectivity_state_comment: str

    def to_html(self) -> str:
        return (
            f"{STARTUP_PROCEDURE__BEGIN_TITLE_HEADERS}\n"
            "   <tr>\n"
            "      <td>Acquire Downstream Channel</td>\n"
            "      <td>975000000 Hz</td>\n"
            "      <td>Locked</td>\n"
            "   </tr>\n"
            "   <tr>\n"
            "      <td>Connectivity State</td>\n"
            f"      <td>{self.connectivity_state}</td>\n"
            f"      <td>{self.connectivity_state_comment}</td>\n"
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
            "      <td>Enabled</td>\n"
            "      <td>BPI+</td>\n"
            "   </tr>\n"
            "   <tr>\n"
            "      <td>DOCSIS Network Access Enabled</td>\n"
            "      <td>Allowed</td>\n"
            "      <td></td>\n"
            "   </tr>\n"
            f"{STARTUP_PROCEDURE__TABLE_END}"
        )


@dataclass
class DownstreamBondedChannelsRow:
    channel_id: int
    lock_status: str
    modulation: str
    frequency_hz: int
    power_dbmv: float
    snr_db: float
    corrected: int
    uncorrectables: int

    def to_html(self) -> str:
        return (
            f"   <tr align='left'>\n"
            f"      <td>{self.channel_id}</td>\n"
            f"      <td>{self.lock_status}</td>\n"
            f"      <td>{self.modulation}</td>\n"
            f"      <td>{self.frequency_hz} Hz</td>\n"
            f"      <td>{self.power_dbmv} dBmV</td>\n"
            f"      <td>{self.snr_db} dB</td>\n"
            f"      <td>{self.corrected}</td>\n"
            f"      <td>{self.uncorrectables}</td>\n"
            f"   </tr>"
        )


@dataclass
class DownstreamBondedChannels:
    rows: list[DownstreamBondedChannelsRow] = field(default_factory=list)

    def to_html(self) -> str:
        rows_html = "\n".join(row.to_html() for row in self.rows)
        return (
            f"{DOWNSTREAM__BEGIN_TITLE_HEADERS}\n"
            f"{rows_html}\n"
            f"{DOWNSTREAM__TABLE_END}"
        )


@dataclass
class UpstreamBondedChannelsRow:
    channel: int
    channel_id: int
    lock_status: str
    channel_type: str
    frequency_hz: int
    width_hz: int
    power_dbmv: float

    def to_html(self) -> str:
        return (
            f"   <tr align='left'>\n"
            f"      <td>{self.channel}</td>\n"
            f"      <td>{self.channel_id}</td>\n"
            f"      <td>{self.lock_status}</td>\n"
            f"      <td>{self.channel_type}</td>\n"
            f"      <td>{self.frequency_hz} Hz</td>\n"
            f"      <td>{self.width_hz} Hz</td>\n"
            f"      <td>{self.power_dbmv} dBmV</td>\n"
            f"   </tr>"
        )


@dataclass
class UpstreamBondedChannels:
    rows: list[UpstreamBondedChannelsRow] = field(default_factory=list)

    def to_html(self) -> str:
        rows_html = "\n".join(row.to_html() for row in self.rows)
        return (
            f"{UPSTREAM__BEGIN_TITLE_HEADERS}\n"
            f"{rows_html}\n"
            f"{UPSTREAM__TABLE_END}"
        )


@dataclass
class ConnectionStatus:
    system_time: datetime | None
    startup: StartupProcedure
    system_time_str: str | None = None
    downstream: DownstreamBondedChannels = field(
        default_factory=DownstreamBondedChannels
    )
    upstream: UpstreamBondedChannels = field(default_factory=UpstreamBondedChannels)

    def __post_init__(self):
        if self.system_time is not None and self.system_time_str is not None:
            raise ValueError("provide system_time or system_time_str, not both")
        if self.system_time_str is None:
            if self.system_time is None:
                raise ValueError("provide system_time or system_time_str")
            self.system_time_str = self.system_time.strftime("%a %b %d %H:%M:%S %Y")

    def to_html(self) -> str:
        return (
            f"{self.startup.to_html()}\n"
            f"{self.downstream.to_html()}\n"
            f"{self.upstream.to_html()}\n"
            f'<p id="systime">'
            f"<strong>Current System Time:</strong> {self.system_time_str}"
            "</p>"
        )
