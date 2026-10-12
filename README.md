# Dogfy Diet - Home Assistant Integration

Custom integration for [Dogfy Diet](https://www.dogfydiet.com) dog food subscription service.

## Features

- Subscription status and amount
- Next order date and status
- Per-dog sensors: weight, daily ration, age

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=agarridob&repository=ha-dogfy-diet&category=integration)

Or manually:

1. In Home Assistant, open **HACS**
2. Open the **⋮** menu (top right) → **Custom repositories**
3. Add `https://github.com/agarridob/ha-dogfy-diet` with type **Integration**
4. Search for **Dogfy Diet** in HACS and click **Download**
5. Restart Home Assistant

### Manual

Copy `custom_components/dogfydiet` from the [latest release](https://github.com/agarridob/ha-dogfy-diet/releases/latest) into your Home Assistant `custom_components` directory and restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up the Dogfy Diet integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=dogfydiet)

1. Go to **Settings → Devices & Services → Add Integration → Dogfy Diet**
2. Log in with your Dogfy Diet email and password

Your password is only used once to obtain a session token; it is not stored. The session is renewed automatically, and if it ever expires Home Assistant will ask you to log in again.

> If you signed up with Google or Apple, set a password first using **Recover password** on [app.dogfydiet.com](https://app.dogfydiet.com/login).

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Dogfy Diet in any way. It is an independent, community-driven integration.
