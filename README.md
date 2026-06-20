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
2. Enter your refresh token

### How to get your refresh token

1. Log in to [app.dogfydiet.com](https://app.dogfydiet.com)
2. Open browser developer tools (F12)
3. Go to **Application → Local Storage → app.dogfydiet.com**
4. Copy the value of `dogfy.refreshToken`

The refresh token is valid for ~120 days and is automatically rotated by the integration.

## Disclaimer

This project is not affiliated with, endorsed by, or connected to Dogfy Diet in any way. It is an independent, community-driven integration.
