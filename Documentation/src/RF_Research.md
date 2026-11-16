# NIGHTHAWK RF research plan and link-budget framework

## What is known and not known
| Item | Status |
|---|---|
| SoluM, Hanshow, Pricer, TagTurk operating frequencies | **Unknown.** Not measured. |
| Hanshow | Sources state 2.4 GHz (Furrtek page; TagTinker README citing Hanshow pages). Unverified by NIGHTHAWK. |
| Pricer | The studied Pricer family is infrared (940 nm, 1.25 MHz carrier, per Furrtek). Not RF. |
| SoluM, TagTurk | No documentation read. |
| Modulation, bandwidth, antenna, range, security | Unknown for all four. |

## Device database
Firmware CSV (`devices.csv`) and desktop SQLite store the 13 fields: manufacturer, model, gateway, revision, frequency, modulation, bandwidth, antenna, approximate range, signal strength, documentation, security, confidence. Unknown values must be stored as `unknown`. Manufacturers are tracked separately.

## Workflow (passive and documentary)
1. Record model/gateway/revision and photograph FCC/CE labels. Look up public regulatory filings for frequency ranges (documentation).
2. Passive survey with external lab receiver or spectrum analyser through RF IN (with attenuator pads populated). Record centre frequency, occupied bandwidth, burst period.
3. Enter results with a confidence level. No compatibility is declared until a module has been tested on that device.
4. Choose a module only after steps 1 to 3.

## Link-budget template (to be filled with measured values)
Received power = P_tx + G_tx - L_cable_tx - L_conn - PL(d) - L_enclosure + G_rx - L_cable_rx.
Margin = Received power - Sensitivity - SNR_required.
Free-space path loss only, for orientation: FSPL(dB) = 20 log10(d_km) + 20 log10(f_MHz) + 32.44. At **2400 MHz**, 10 m = 80.0 dB, 20 m = 86.0 dB. 2400 MHz is a placeholder, not a verified target frequency. Indoor loss, antenna pattern and enclosure attenuation add to this and are unmeasured.

| Quantity | Value |
|---|---|
| External generator output | to be set by lab equipment, not by this board |
| Receiver sensitivity | depends on the future module |
| Antenna gain | depends on the future module |
| Cable and connector loss | measure |
| Enclosure attenuation | measure |

The 10 to 20 m target is **not** demonstrated. Whether a future module can support it is decided after the frequency is known.

## Compliance
Conducted tests use attenuated connections to owned equipment. OTA tests only in a shielded enclosure. The board has no transmitter.
