# Dogfy Diet - Home Assistant Integration

Custom integration for [Dogfy Diet](https://www.dogfydiet.com) dog food subscription service.

## Features

- Subscription status and amount
- Next order date and status
- Per-dog sensors: weight, daily ration, age

## Installation

Copy `custom_components/dogfydiet` into your Home Assistant `custom_components` directory.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration → Dogfy Diet**
2. Log in with your Dogfy Diet email and password

Your password is only used once to obtain a session token; it is not stored. The session is renewed automatically, and if it ever expires Home Assistant will ask you to log in again.

> If you signed up with Google or Apple, set a password first using **Recover password** on [app.dogfydiet.com](https://app.dogfydiet.com/login).

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Dogfy Diet in any way. It is an independent, community-driven integration.
