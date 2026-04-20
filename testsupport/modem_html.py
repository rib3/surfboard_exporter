from dataclasses import dataclass, field
from datetime import datetime

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
            f"{self.downstream.to_html()}\n"
            f"{self.upstream.to_html()}\n"
            f'<p id="systime">'
            f"<strong>Current System Time:</strong> {self.system_time_str}"
            "</p>"
        )
