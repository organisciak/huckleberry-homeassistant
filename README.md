# Huckleberry Home Assistant Integration (fork)

Home Assistant custom integration for the Huckleberry baby tracking app.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=organisciak&repository=huckleberry-homeassistant&category=integration)

> **This is a fork of [Woyken/huckleberry-homeassistant](https://github.com/Woyken/huckleberry-homeassistant).**
> All the original work is Woyken's; this fork exists to add two things (see [Why this fork exists](#why-this-fork-exists)). I quickly forked this while sleepless with my own baby — I hope to contribute the fixes upstream, and others are welcome to.

## Why this fork exists

This fork is based on upstream **v0.4.3** and adds two changes:

1. **🫛 Pumping support** — the upstream integration tracks nursing and bottle feeds but never exposed pumping, even though the underlying [`huckleberry-api`](https://pypi.org/project/huckleberry-api/) library already implements it. This fork wires it up: a `huckleberry.log_pump` service, a `sensor.{child}_pumping` sensor, and pump events in the calendar.

2. **🩹 `get_events` crash-fix** — rendering `calendar.{child}_events` on an always-on dashboard surface (Google Cast / wall kiosk) drove frequent `calendar.get_events` calls, each fanning out several Firestore streaming queries over the same gRPC channel the realtime listeners use. Under sustained load this saturated the asyncio event loop and put Home Assistant into a crash/restart loop. This fork **coalesces and caches** `async_get_events` (90 s TTL per time-window, plus an `asyncio.Lock` so concurrent identical requests don't each fan out), which keeps bursty dashboard refreshes from starving the shared channel.

## Overview

This integration provides real-time baby tracking in Home Assistant by connecting to Huckleberry's Firebase backend using the [`huckleberry-api`](https://pypi.org/project/huckleberry-api/) Python library.

## Features

- 💤 **Sleep Tracking**: Sensors, switches, and automation services
- 🤱 **Nursing Tracking**: Left/right side tracking with switches and services
- 🍼 **Bottle Feeding**: Log bottle feeds with amount and type
- 🫛 **Pumping** *(fork)*: Log pumping sessions and track the last session
- 🧷 **Diaper Changes**: Log pee, poo, both, or dry checks
- 📏 **Growth Measurements**: Track weight, height, head circumference
- 📅 **Calendar**: Historical events per child in HA's calendar view (cached/coalesced to protect the shared gRPC channel — *fork*)
- 🔄 **Real-time Sync**: Instant updates via Firebase listeners
- 👶 **Multi-child Support**: Separate devices per child

## Installation

### HACS (Recommended)

1. In HACS, open the **⋮** menu → **Custom repositories**, add `https://github.com/organisciak/huckleberry-homeassistant` with category **Integration** (or use the badge above).
2. Search for **Huckleberry**, open it, and click **Download**.
3. Restart Home Assistant.

> **Replacing an existing Huckleberry install?** HACS won't show this fork while another repository already provides the `huckleberry` integration domain. Remove the currently-installed Huckleberry from HACS first (this deletes only the code — your account login, child config, devices, and history are kept in HA's core storage), restart HA, then add this fork. Your existing config entry reloads against the fork's code, so no re-login is needed.

### Manual Installation

1. Copy the `custom_components/huckleberry` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Huckleberry"
4. Enter your Huckleberry account email and password
5. Click Submit

## Entities Created

### Per Child:
- **Sensors**:
  - `sensor.{child_name}_sleep` - Sleep status (sleeping, paused, none)
  - `sensor.{child_name}_nursing` - Nursing status (nursing, paused, none)
  - `sensor.{child_name}_profile` - Child profile information
  - `sensor.{child_name}_growth` - Latest growth measurements
  - `sensor.{child_name}_bottle` - Last bottle feeding (time, amount, type)
  - `sensor.{child_name}_pumping` - Last pumping session (time, amount, left/right, units, duration) *(fork)*
  - `sensor.{child_name}_diaper` - Last diaper change

- **Switches** (3):
  - `switch.{child_name}_sleep_timer` - Start/stop the sleep timer
  - `switch.{child_name}_nursing_left` - Left side nursing
  - `switch.{child_name}_nursing_right` - Right side nursing

- **Calendar** (1):
  - `calendar.{child_name}_events` - All historical events (sleep, nursing, bottle, pumping, diaper, growth, health)

### Global:
- `sensor.huckleberry_children` - Number of children

## Services

All services support device selection for easy use in automations:

### Sleep Tracking
- `huckleberry.start_sleep`
- `huckleberry.pause_sleep`
- `huckleberry.resume_sleep`
- `huckleberry.cancel_sleep`
- `huckleberry.complete_sleep`

### Nursing Tracking
- `huckleberry.start_nursing`
- `huckleberry.pause_nursing`
- `huckleberry.resume_nursing`
- `huckleberry.switch_nursing_side`
- `huckleberry.cancel_nursing`
- `huckleberry.complete_nursing`

### Bottle Feeding
- `huckleberry.log_bottle` - Log bottle feeding (formula or breastmilk) with amount in oz or ml

### Pumping *(fork)*
- `huckleberry.log_pump` - Log a pumping session; `total_amount` is split evenly across both sides by the library. Optional `units` (ml/oz), `duration` (seconds), and `notes`.

### Diaper Changes
- `huckleberry.log_diaper_pee`
- `huckleberry.log_diaper_poo`
- `huckleberry.log_diaper_both`
- `huckleberry.log_diaper_dry`

### Growth Tracking
- `huckleberry.log_growth`

## Calendar

Each child gets a calendar entity that displays all historical events:

- **💤 Sleep events**: Shows duration and timing of all sleep sessions
- **🍼 Feeding events**: Shows duration, left/right side information
- **🫛 Pump events** *(fork)*: Shows total amount and left/right split
- **🩲 Diaper changes**: Shows type (pee/poo/both/dry) and details
- **📏 Growth measurements**: Shows weight, height, head circumference

The calendar can be added to dashboards and used in automations. Events are automatically fetched when you view the calendar for a specific date range, and are cached briefly (90 s per window) so always-on dashboards don't overwhelm the backend.

### Adding to Dashboard

Add the calendar card to your dashboard:
```yaml
type: calendar
entities:
  - calendar.baby_name_events
```

## Example Automations

See `automation_examples.yaml` for complete examples.

### Bedtime Notification
```yaml
automation:
  - alias: "Baby Sleep Started"
    trigger:
      - platform: state
        entity_id: sensor.baby_name_sleep
        to: "sleeping"
    action:
      - service: notify.mobile_app
        data:
          message: "Baby started sleeping"
```

### Feeding Timer Alert
```yaml
automation:
  - alias: "Nursing Duration Alert"
    trigger:
      - platform: state
        entity_id: sensor.baby_name_nursing
        to: "nursing"
        for:
          minutes: 20
    action:
      - service: notify.mobile_app
        data:
          message: "Baby has been nursing for 20 minutes"
```

### Log Bottle Feeding
```yaml
automation:
  - alias: "Log Bottle at Scheduled Time"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: huckleberry.log_bottle
        target:
          device_id: YOUR_DEVICE_ID  # Select your child's device
        data:
          amount: 120.0
          bottle_type: Formula
          units: ml
```

### Log Pumping *(fork)*
```yaml
automation:
  - alias: "Log Pumping Session"
    trigger:
      - platform: state
        entity_id: input_button.log_pump  # e.g. a dashboard button
    action:
      - service: huckleberry.log_pump
        target:
          device_id: YOUR_DEVICE_ID  # Select your child's device
        data:
          total_amount: 120.0
          units: ml
```

## Device Actions

Device actions were removed upstream in v0.4.0. Use HA services instead — they support the same `device_id` selector in the automation editor. See [Services](#services) above.

## Development

- `uv sync --dev`
- `uv run ruff check .`
- `uv run ty check`
- `uv run pytest`

## Requirements

- Home Assistant 2026.3 or newer
- Huckleberry account
- `huckleberry-api==0.4.3` (automatically installed; required for pumping support)

## Support

This is a personal fork. For bugs in the original integration, please open an issue on the [upstream repository](https://github.com/Woyken/huckleberry-homeassistant/issues). For issues specific to the fork's changes, open an issue here.

## Related Projects

- [Woyken/huckleberry-homeassistant](https://github.com/Woyken/huckleberry-homeassistant) - the upstream integration this is forked from
- [huckleberry-api](https://github.com/Woyken/huckleberry-api) - Python API library used by this integration

## Disclaimer

This is an unofficial, community-developed integration. Not affiliated with, endorsed by, or connected to Huckleberry Labs Inc.

## License

MIT License
