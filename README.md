# Zynq7010 / PlutoSDR QRSS Beacon

**Created by SV1EEX**

A lightweight Python GUI for generating slow CW / QRSS beacon transmissions with Analog Devices PlutoSDR and compatible Zynq7000 + AD936x SDR hardware.

The program uses the FPGA DDS exposed by the Analog Devices IIO stack, so the host computer does not need to continuously stream IQ samples during a transmission. Python is used mainly for beacon timing, Morse generation, parameter control and the graphical interface.

## Features

* Tkinter graphical interface
* PlutoSDR and compatible Zynq7000 + AD936x support
* IIO connection over Ethernet or another libiio URI
* FPGA DDS based CW generation
* QRSS1, QRSS3, QRSS6 and QRSS10 modes
* Configurable RF frequency
* Configurable DDS offset
* Configurable TX attenuation from the GUI
* Configurable DDS amplitude
* User defined beacon message
* Repeat interval control
* Two second CW carrier test
* Immediate software stop request using an interruptible worker thread
* DDS shutdown when a transmission finishes
* Hardware emergency stop reminder for boards fitted with an RST button

## Tested hardware

Development was performed with a Pluto compatible board reporting itself through libiio as:

```text
Analog Devices PlutoSDR Rev.B (Z7010-AD9364)
```

The detected FPGA design exposes the standard Analog Devices transmit DDS device:

```text
cf-ad9361-dds-core-lpc
```

The same approach should work with genuine PlutoSDR units and other compatible AD936x based designs that expose the same DDS interface. Compatibility cannot be guaranteed for custom FPGA images that omit or modify the DDS core.

## Requirements

The project requires Python and the Analog Devices IIO software stack.

Python packages:

```text
pyadi-iio
pylibiio
```

Install them with:

```bash
python -m pip install -r requirements.txt
```

On Windows, the native Analog Devices libiio runtime and drivers must also be installed if they are not already present.

A quick installation check is:

```bash
python -c "import adi; import iio; print('ADI:', adi.__version__); print('IIO:', iio.version)"
```

You can verify that the SDR is visible with:

```bash
iio_info -S
```

For a typical Pluto network connection:

```bash
iio_info -u ip:192.168.2.1
```

## Running the program

Clone or download the repository and run:

```bash
python qrss_beacon.py
```

The default IIO URI is:

```text
ip:192.168.2.1
```

Change this in the GUI if your SDR uses a different address or libiio URI.

## Frequency generation

The application deliberately places the FPGA DDS tone away from zero Hz rather than generating the wanted carrier directly at DC.

For example:

```text
Wanted RF frequency     144.400000 MHz
DDS offset                0.100000 MHz
TX LO                   144.300000 MHz

TX LO + DDS offset = wanted RF frequency
```

This helps separate the wanted signal from LO leakage and DC related artifacts that may appear around the SDR local oscillator frequency.

The default sample rate is:

```text
3.84 MHz
```

The default DDS offset is:

```text
100 kHz
```

## QRSS timing

The selected mode determines the Morse dot duration.

| Mode | Dot | Dash |
| --- | ---: | ---: |
| QRSS1 | 1 s | 3 s |
| QRSS3 | 3 s | 9 s |
| QRSS6 | 6 s | 18 s |
| QRSS10 | 10 s | 30 s |

Standard Morse spacing is used inside the application. The long symbol durations make QRSS suitable for narrow bandwidth reception and waterfall observation.

## TX level controls

The GUI exposes two different level controls.

`TX gain dB` controls the AD936x transmit attenuation setting. On the development hardware the available range is approximately:

```text
-89.75 dB to 0 dB
```

`DDS amplitude` controls the FPGA DDS scale. A value of `1.0` is full scale at the DDS level.

These controls do not directly specify RF power in watts or dBm. Actual output power depends on the SDR hardware, frequency, calibration, filtering and any external RF stages.

## Stopping transmission

`STOP TX` sets an interrupt event used by the transmission worker. Symbol timing and repeat delays use interruptible waits so the worker can leave the transmit sequence promptly and disable the DDS.

When the software stop sequence completes, the status returns to:

```text
CONNECTED / TX OFF
```

If software control is lost and the hardware provides a physical `RST` button, pressing `RST` reboots the SDR and provides a direct way to terminate the active FPGA DDS state. This is intended only as a recovery measure rather than normal operation.

## Checking the transmitted signal

A second SDR and waterfall display are the easiest way to verify operation.

For a first test, use the `2 SECOND CW TEST` button and monitor the selected RF frequency with an independent receiver. Avoid overloading the receiving SDR. A nearby transmitter can produce receiver overload, images and apparent spurious signals that are not representative of the transmitter output.

For QRSS observation, a narrow waterfall display is preferable because the signal changes very slowly.

## Important operating note

This software can cause the connected SDR to transmit RF energy. The operator is responsible for selecting frequencies, power levels, identification methods and operating conditions that comply with the applicable amateur radio licence, national regulations and relevant band plan.

The example frequencies in this project are configuration examples and are not a recommendation to operate a beacon on a particular frequency.

## Project structure

```text
qrssbeaconplutosdr/
    qrss_beacon.py
    requirements.txt
    README.md
```

## Current scope

The current version implements amplitude keyed slow CW using the FPGA DDS.

Possible future additions include FSKCW, configurable Morse spacing, saved profiles, frequency calibration assistance, persistent configuration and waterfall oriented beacon modes.

## Author

**SV1EEX**

GitHub: `z1000biker`

Repository: `z1000biker/qrssbeaconplutosdr`
