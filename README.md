# Fitdays for Home Assistant

[![hacs][hacs-badge]][hacs]

Home Assistant integration for Fitdays and ICOMON smart scales: the Robi S6 and
the rebadged body-composition scales that use the Fitdays app.

Your scale computes fat, muscle, water, bone mass, BMR and body age from
bio-impedance, uploads them, and then they stay inside the app. This integration
reads them into Home Assistant.

## Why not Bluetooth?

The other smart-scale options in Home Assistant read the scale over BLE. That
costs you three things.

Home Assistant has to be in Bluetooth range at the moment you step on, or the
weigh-in is lost. You get weight and little else, because the body-composition
maths runs in the vendor's cloud rather than on the scale. And you get no
history from before the day you set it up.

This integration reads the Fitdays cloud instead, so a weigh-in lands in Home
Assistant wherever you took it, with every metric and your existing history.

## Features

- One device per person. A Fitdays account can hold several member profiles, and
  each becomes its own Home Assistant device, so a shared scale does not produce
  one ambiguous pile of sensors. A profile added in the app appears without a
  reload.
- Body composition: weight, BMI, body fat in percent and kg, muscle in percent
  and kg, skeletal muscle, body water, bone mass, protein, subcutaneous and
  visceral fat, BMR, body age and impedance.
- Target weight and the distance to it.
- `last_measurement` is a timestamp sensor, so an automation can trigger on a new
  weigh-in.
- Diagnostics, system health, and English and Dutch translations.

## Installation

### HACS

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/AboveColin/HA-Fitdays`, category **Integration**
3. Install **Fitdays**, then restart Home Assistant

### Manual

Copy `custom_components/fitdays` into your `config/custom_components/` directory and
restart.

## Configuration

**Settings → Devices & Services → Add Integration → Fitdays**

Enter the email and password you use in the Fitdays app, plus the two-letter
country code your account is registered in, `NL` by default.

Your password is hashed (double MD5, exactly as the app does it) before anything
leaves Home Assistant, and only that digest is stored in the config entry, never
the plaintext. The digest is what lets the integration silently renew an expired
session without asking you to log in again.

## Entities

Per member profile:

| Sensor | Notes |
|---|---|
| Weight | kg, with measurement context as attributes |
| BMI | |
| Body fat | %, with Body fat mass in kg as a second sensor |
| Muscle | %, with Muscle mass in kg as a second sensor |
| Skeletal muscle | % (mass variant disabled by default) |
| Body water | % (mass variant disabled by default) |
| Bone mass | kg |
| Protein | % (mass variant disabled by default) |
| Visceral fat | index |
| Basal metabolic rate | kcal |
| Body age | years |
| Last measurement | timestamp |
| Subcutaneous fat, Heart rate, Impedance, Target weight, Weight to target, Measurements | disabled by default, enable as needed |

Heart rate only reports on scales that measure it (`measures_heart_rate` on the
device). On a scale without it the sensor stays *unknown*, not *unavailable*.

## Notes and limitations

- Cloud polling every 30 minutes. A scale gets stepped on a couple of times a
  day, so polling harder buys nothing.
- A weigh-in taken without proper skin contact comes back weight-only, with no
  impedance and so no body composition. The body-composition sensors go to
  unknown for that weigh-in rather than holding their previous value, and the
  `weight_only` attribute on the weight sensor says why.
- The integration is read-only. It never writes to your Fitdays account.
- Brand artwork in `custom_components/fitdays/brand/` is a generic placeholder
  glyph, not the vendor's logo. Home Assistant reads that folder from 2026.3.0
  onward; on older cores the integration renders without an icon.

## Disclaimer

Not affiliated with or supported by GUANGDONG ICOMON or Fitdays. Built on
[`fitdays`](https://github.com/AboveColin/fitdays), an unofficial client derived
from the app's own traffic. The endpoints can change without notice.

## Licence

MIT, see [LICENSE](LICENSE).

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
