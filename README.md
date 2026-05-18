# surfboard_exporter

Prometheus exporter for Arris SURFBoard SB8200 cable modems.

## Install

Requires Python 3.12+.

`pip install git+https://github.com/rib3/surfboard_exporter.git`

## Configuration

Precedence (per setting): CLI > env > `.env` > secrets dir (if enabled) > default.

| Env Var                              | CLI Flag                          | Default           | Notes |
| ------------------------------------ | --------------------------------- | ----------------- | ----- |
| `SURFBOARD_PASSWORD`                 | `--password`                      | *(required)*      | Modem admin password. **Warning:** prefer env (or file); `--password …` is visible via `ps`/`/proc`. |
| `SURFBOARD_PASSWORD_FILE`            | `--password-file`                 | unset             | Path to file containing password; overrides `SURFBOARD_PASSWORD`. |
| `SURFBOARD_USERNAME`                 | `--username`                      | `admin`           |  |
| `SURFBOARD_MODEM_HOST`               | `--modem-host`                    | `192.168.100.1`   |  |
| `SURFBOARD_MODEM_CERTIFICATE_VERIFY` | `--[no-]modem-certificate-verify` | `true`            | `false` disables TLS verify. |
| `SURFBOARD_MODEM_CERTIFICATE_FILE`   | `--modem-certificate-file`        | unset             | Path to modem cert, for (quirk-tolerant) TLS verification. |
| `SURFBOARD_LISTEN_HOST`              | `--listen-host`                   | `0.0.0.0`         | HTTP bind address. |
| `SURFBOARD_LISTEN_PORT`              | `--listen-port`                   | `9779`            | HTTP port to serve metrics on. |
| `SURFBOARD_VERBOSE`                  | `-v`, `--[no-]verbose`            | `false`           | Increase logging. |
| `SURFBOARD_LOG_FILE`                 | `--[no-]log-file`                 | `false`           | Write logs to `exporter.log`. |
| `SURFBOARD_RESPONSE_SAVE`            | `--[no-]response-save`            | `false`           | Dump modem responses to file(s) (for debugging). |
| `SURFBOARD_SECRETS_DIR`              | —                                 | unset             | Directory of per-setting files (e.g. `/run/secrets` for container secrets). |
| `TMPDIR`                             | `--tmpdir`                        | system default    | Override tempdir (base for per-pid temp dir). |

Typical:

- `SURFBOARD_PASSWORD`
- `SURFBOARD_MODEM_CERTIFICATE_FILE`
  - or `SURFBOARD_MODEM_CERTIFICATE_VERIFY=false`

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

## Development

### Setup

Setup Environment variables (see [Configuration](#configuration)).
- via a `.env` file (recommended in the project root) ([gitignored](.gitignore))
- manually

### Commands

- `make http` — run collector http server
  - `make http-dev` — http + auto-restart on file changes
  - pass additional args via `ARGS=`
    - `make http-dev ARGS="--response-save --log-file"`
- `pytest`
- `make lint` / `make lint-fix`

## License

Apache-2.0. See [LICENSE](LICENSE).

Copyright 2026 Bob Black
