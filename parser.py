from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup


@dataclass
class DownstreamChannel:
    channel_id: int
    lock_status: str
    modulation: str
    frequency_hz: int
    power_dbmv: float
    snr_db: float
    corrected: int
    uncorrectables: int


def parse_downstream_channels(html: str) -> list[DownstreamChannel]:
    soup = BeautifulSoup(html, "html.parser")

    header = soup.find("th", string=lambda t: t and "Downstream Bonded Channels" in t)
    table = header.find_parent("table")

    channels = []
    for row in table.find_all("tr")[2:]:  # skip header rows
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) != 8:
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
