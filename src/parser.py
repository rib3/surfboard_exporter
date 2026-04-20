import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass
class ConnectivityState:
    ok: float
    comment: str


@dataclass
class Security:
    enabled: float
    comment: str


@dataclass
class DownstreamChannel:
    channel_id: int
    lock_status: str
    locked: bool = field(init=False)
    modulation: str
    frequency_hz: int
    power_dbmv: float
    snr_db: float
    corrected: int
    uncorrectables: int

    def __post_init__(self):
        self.locked = self.lock_status == "Locked"


@dataclass
class UpstreamChannel:
    channel_id: int
    lock_status: str
    locked: bool = field(init=False)
    channel_type: str
    frequency_hz: int
    width_hz: int
    power_dbmv: float

    def __post_init__(self):
        self.locked = self.lock_status == "Locked"


def parse_system_time(html: str) -> float:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("p", id="systime")
    if tag is not None:
        try:
            text = tag.get_text(strip=True)
            time_str = text.removeprefix("Current System Time:").strip()
            return datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y").timestamp()
        except ValueError:
            logger.exception("failed to parse system time")

    return float("nan")


def _trs_for_table(
    html: str,
    title_substring: str,
    *,
    skip: int = 0,
) -> Iterator[Tag]:
    soup = BeautifulSoup(html, "html.parser")
    header = soup.find("th", string=lambda t: t and title_substring in t)
    if header is None:
        logger.warning("table with th content %r not found", title_substring)
        return
    table = header.find_parent("table")
    yield from table.find_all("tr")[skip:]


def _text_rows_for_table(
    html: str,
    title_substring: str,
    *,
    skip: int = 0,
    tds_required: int,
) -> Iterator[list[str]]:
    for row in _trs_for_table(html, title_substring, skip=skip):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) != tds_required:
            logger.warning(
                "skipping row, len(cells)=%d != %d:\n%r",
                len(cells),
                tds_required,
                str(row),
            )
            continue
        yield cells


def _parse_startup_row(
    html: str,
    row_label: str,
    truthy_status: str,
) -> tuple[float, str]:
    for row in _trs_for_table(html, "Startup Procedure"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if cells[:1] == [row_label] and cells[1:2]:
            value = 1.0 if cells[1] == truthy_status else 0.0
            comment = cells[2] if cells[2:3] else ""
            return value, comment
    logger.warning("%s row not found:\n%r", row_label, html)
    return float("nan"), ""


def parse_connectivity_state(html: str) -> ConnectivityState:
    ok, comment = _parse_startup_row(html, "Connectivity State", "OK")
    return ConnectivityState(ok=ok, comment=comment)


def parse_security(html: str) -> Security:
    enabled, comment = _parse_startup_row(html, "Security", "Enabled")
    return Security(enabled=enabled, comment=comment)


def parse_downstream_channels(html: str) -> list[DownstreamChannel]:
    # skip header row(s); malformed html combines title and column headers in one tr
    return [
        DownstreamChannel(
            channel_id=int(cells[0]),
            lock_status=cells[1],
            modulation=cells[2],
            frequency_hz=int(cells[3].removesuffix(" Hz")),
            power_dbmv=float(cells[4].removesuffix(" dBmV")),
            snr_db=float(cells[5].removesuffix(" dB")),
            corrected=int(cells[6]),
            uncorrectables=int(cells[7]),
        )
        for cells in _text_rows_for_table(
            html, "Downstream Bonded Channels", skip=1, tds_required=8
        )
    ]


def parse_upstream_channels(html: str) -> list[UpstreamChannel]:
    # skip header row(s); malformed html combines title and column headers in one tr
    return [
        UpstreamChannel(
            channel_id=int(cells[1]),
            lock_status=cells[2],
            channel_type=cells[3],
            frequency_hz=int(cells[4].removesuffix(" Hz")),
            width_hz=int(cells[5].removesuffix(" Hz")),
            power_dbmv=float(cells[6].removesuffix(" dBmV")),
        )
        for cells in _text_rows_for_table(
            html, "Upstream Bonded Channels", skip=1, tds_required=7
        )
    ]
