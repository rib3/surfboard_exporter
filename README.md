# surfboard_exporter

Prometheus exporter for Arris SURFBoard SB8200 cable modems.

## Install

Requires Python 3.12+.

`pip install git+https://github.com/rib3/surfboard_exporter.git`

## Environment

| Variable                            | Default           | Notes                                    |
| ----------------------------------- | ----------------- | ---------------------------------------- |
| `SURFBOARD_PASSWORD`                | *(required)*      | Modem admin password.                    |
| `SURFBOARD_PASSWORD_FILE`           | unset             | Path to file containing password; overrides `SURFBOARD_PASSWORD`. |
| `SURFBOARD_USERNAME`                | `admin`           |                                          |
| `SURFBOARD_MODEM_HOST`              | `192.168.100.1`   |                                          |
| `SURFBOARD_MODEM_CERTIFICATE_VERIFY`| `true`            | JSON bool. `false` disables TLS verify.  |
| `SURFBOARD_MODEM_CERTIFICATE_PATH`  | unset             | Path to modem cert, for (quirk-tolerant) TLS verification. |

Typical:

- `SURFBOARD_PASSWORD`
- `SURFBOARD_MODEM_CERTIFICATE_PATH`
  - or `SURFBOARD_MODEM_CERTIFICATE_VERIFY=false`

## Options

- `--listen-host` — HTTP bind address (default `0.0.0.0`)
- `--listen-port` — HTTP port to serve metrics on (default `9779`)
- `-v`, `--verbose` — increase logging
- `--log-file` — write logs to `exporter.log`
- `--response-save` — dump modem responses to file(s) (for debugging)

Logs/files are written to a per-pid temp dir
(`$TMPDIR/surfboard_exporter.<pid>.<rand>/`).

## Metrics

- `surfboard_scrape_success`
- `surfboard_ssl_verify`
- `surfboard_system_time`
- `surfboard_connectivity_state_ok{comment}`
- `surfboard_security_enabled{comment}`
- `surfboard_docsis_network_access_allowed{comment}`
- `surfboard_upstream_locked{channel_id,lock_status}`
- `surfboard_upstream_frequency_hz{channel_id}`
- `surfboard_upstream_width_hz{channel_id}`
- `surfboard_upstream_power_dbmv{channel_id}`
- `surfboard_downstream_locked{channel_id,lock_status}`
- `surfboard_downstream_frequency_hz{channel_id}`
- `surfboard_downstream_power_dbmv{channel_id}`
- `surfboard_downstream_snr_db{channel_id}`
- `surfboard_downstream_corrected{channel_id}`
- `surfboard_downstream_uncorrectables{channel_id}`

## License

Apache-2.0. See [LICENSE](LICENSE).

Copyright 2026 Bob Black
