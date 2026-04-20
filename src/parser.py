import logging
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


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


def parse_connectivity_state_ok(html: str) -> float:
    soup = BeautifulSoup(html, "html.parser")
    header = soup.find("th", string=lambda t: t and "Startup Procedure" in t)
    if header is None:
        logger.warning("Startup Procedure header not found:\n%r", html)
        return float("nan")
    table = header.find_parent("table")
    for row in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if cells[:1] == ["Connectivity State"] and cells[1:2]:
            return 1.0 if cells[1] == "OK" else 0.0
    logger.warning("Connectivity State row not found:\n%r", html)
    return float("nan")


def parse_downstream_channels(html: str) -> list[DownstreamChannel]:
    soup = BeautifulSoup(html, "html.parser")

    header = soup.find("th", string=lambda t: t and "Downstream Bonded Channels" in t)
    if header is None:
        logger.warning("header not found:\n%r", html)
        return []
    table = header.find_parent("table")

    channels = []
    # skip header row(s); malformed html combines title and column headers in one tr
    for row in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) != 8:
            logger.warning(
                "skipping row, len(cells)=%d != 8:\n%r", len(cells), str(row)
            )
            continue
        channels.append(
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
        )
    return channels


def parse_upstream_channels(html: str) -> list[UpstreamChannel]:
    soup = BeautifulSoup(html, "html.parser")

    header = soup.find("th", string=lambda t: t and "Upstream Bonded Channels" in t)
    if header is None:
        logger.warning("header not found:\n%r", html)
        return []
    table = header.find_parent("table")

    channels = []
    # skip header row(s); malformed html combines title and column headers in one tr
    for row in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) != 7:
            logger.warning(
                "skipping row, len(cells)=%d != 7:\n%r", len(cells), str(row)
            )
            continue
        channels.append(
            UpstreamChannel(
                channel_id=int(cells[1]),
                lock_status=cells[2],
                channel_type=cells[3],
                frequency_hz=int(cells[4].removesuffix(" Hz")),
                width_hz=int(cells[5].removesuffix(" Hz")),
                power_dbmv=float(cells[6].removesuffix(" dBmV")),
            )
        )
    return channels
