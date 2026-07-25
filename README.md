# Fitdays for Home Assistant

[![hacs][hacs-badge]][hacs]

Home Assistant integration for **Fitdays / ICOMON smart scales** — the Robi S6 and
the family of rebadged body-composition scales that use the Fitdays app.

Your scale already measures fat, muscle, water, bone mass, BMR and body age. It
computes them from bio-impedance, uploads them, and then they live only inside the
app. This integration brings them into Home Assistant.

## Why not Bluetooth?

Every other smart-scale option in Home Assistant reads the scale over BLE, which
means:

* Home Assistant has to be in Bluetooth range **at the moment you step on**, or the
  weigh-in is simply lost.
* You get weight, and little else — the body-composition maths happens in the
  vendor's cloud, not on the scale.
* No history: nothing before the day you set it up.

This integration talks to the Fitdays cloud instead, so every measurement lands in
Home Assistant regardless of where you weighed yourself, with the full set of
metrics and your existing history behind it.

## Features

- **One device per person.** A Fitdays account can hold several member profiles;
  each becomes its own Home Assistant device, so a shared scale doesn't produce one
  ambiguous pile of sensors. Profiles added in the app later appear without a reload.
- **Full body composition** — weight, BMI, body fat (% and kg), muscle (% and kg),
  skeletal muscle, body water, bone mass, protein, subcutaneous and visceral fat,
  BMR, body age, and impedance.
- **Goal tracking** — target weight and how far you are from it.
- **Local-history-friendly** — `last_measurement` is a proper timestamp sensor, so
  automations can react to a new weigh-in.
- Diagnostics + system health, English and Dutch translations.

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

Enter the email and password you use in the Fitdays app, plus the two-letter country
code your account is registered in (`NL` by default).

Your password is hashed (double MD5, exactly as the app does it) before anything
leaves Home Assistant, and only that digest is stored in the config entry — never
the plaintext. The digest is what lets the integration silently renew an expired
session instead of nagging you to log in again.

## Entities

Per member profile:

| Sensor | Notes |
|---|---|
| Weight | kg, with measurement context as attributes |
| BMI | |
| Body fat | % — and *Body fat mass* in kg |
| Muscle | % — and *Muscle mass* in kg |
| Skeletal muscle | % (mass variant disabled by default) |
| Body water | % (mass variant disabled by default) |
| Bone mass | kg |
| Protein | % (mass variant disabled by default) |
| Visceral fat | index |
| Basal metabolic rate | kcal |
| Body age | years |
| Last measurement | timestamp |
| Subcutaneous fat, Heart rate, Impedance, Target weight, Weight to target, Measurements | disabled by default — enable as needed |

Heart rate only reports on scales that measure it (`measureHeart`), and stays
unavailable otherwise.

## Notes and limitations

- **Cloud polling**, every 30 minutes. Scales are stepped on a couple of times a
  day, so there is nothing to gain from polling harder.
- Weigh-ins taken without proper skin contact come back **weight-only** — no
  impedance, so no body composition. Those sensors hold their last known good value
  and the `weight_only` attribute on the weight sensor flags it.
- The integration is **read-only**. It never modifies your Fitdays account.
- Brand artwork in `custom_components/fitdays/brand/` is a generic placeholder
  glyph, not the vendor's logo.

## Disclaimer

Not affiliated with, endorsed by, or supported by GUANGDONG ICOMON or Fitdays. Built
on [`fitdays`](https://github.com/AboveColin/fitdays), an unofficial client derived
from the app's own traffic. Endpoints may change without notice.

## Licence

MIT — see [LICENSE](LICENSE).

[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
