from dataclasses import dataclass, field


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
            '<table class="simpleTable">\n'
            "<tbody>\n"
            "<tr><th colspan=8><strong>Downstream Bonded Channels</strong></th></tr>\n"
            "      <td><strong>Channel ID</strong></td>\n"
            "      <td><strong>Lock Status</strong></td>\n"
            "      <td><strong>Modulation</strong></td>\n"
            "      <td><strong>Frequency</strong></td>\n"
            "      <td><strong>Power</strong></td>\n"
            "      <td><strong>SNR/MER</strong></td>\n"
            "      <td><strong>Corrected</strong></td>\n"
            "      <td><strong>Uncorrectables</strong></td>\n"
            "   </tr>\n"
            f"{rows_html}\n"
            "</tbody>\n"
            "</table>"
        )


@dataclass
class UpstreamBondedChannels:
    rows: list[UpstreamBondedChannelsRow] = field(default_factory=list)

    def to_html(self) -> str:
        rows_html = "\n".join(row.to_html() for row in self.rows)
        return (
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
            f"{rows_html}\n"
            "</tbody>\n"
            "</table>"
        )
