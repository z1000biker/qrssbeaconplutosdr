# Zynq7010 / PlutoSDR QRSS Beacon

**Created by SV1EEX**

An embedded SDR QRSS transmitter project for Analog Devices PlutoSDR and compatible Zynq7000 + AD936x platforms.

The project contains two implementations of the same beacon concept:

1. A Python/Tkinter desktop controller using `pyadi-iio`.
2. A fully standalone shell implementation that runs directly on the Zynq ARM Linux system and controls the FPGA DDS through IIO sysfs.

The standalone mode does not require a host computer once installed on the SDR.

## Why this approach

The beacon does not continuously stream IQ samples from a PC. Carrier generation is performed by the FPGA DDS exposed by the Analog Devices IIO architecture. The host or embedded ARM processor only performs configuration and slow Morse timing.

This keeps the transmit path simple and makes autonomous operation practical.

## Features

* PlutoSDR and compatible Zynq7000 + AD936x support
* FPGA DDS based RF carrier generation
* QRSS CW transmission
* Configurable RF frequency
* Configurable DDS offset
* Configurable AD936x TX attenuation
* Configurable DDS amplitude
* User defined Morse identification
* Configurable repeat interval
* QRSS1, QRSS3, QRSS6 and QRSS10 in the Python GUI
* Two second carrier test in the Python GUI
* Controlled DDS shutdown
* Standalone embedded Linux operation
* No PC required in standalone mode
* Persistent installation through `/mnt/jffs2` on compatible Pluto firmware

## Tested hardware

Development and RF testing were performed with a Pluto compatible board reporting through libiio as:

```text
Analog Devices PlutoSDR Rev.B (Z7010-AD9364)
```

The board exposes:

```text
iio:device0: ad9361-phy
iio:device2: cf-ad9361-dds-core-lpc
```

The transmit DDS channels used by the standalone implementation are:

```text
TX1_I_F1
TX1_Q_F1
```

The same architecture should also work with genuine PlutoSDR units and other compatible AD936x designs that expose the standard Analog Devices DDS interfaces. Custom FPGA images may differ.

## Repository structure

```text
qrssbeaconplutosdr/
    qrss_beacon.py      Python/Tkinter desktop GUI
    qrss_beacon.sh      Standalone embedded Linux beacon
    requirements.txt    Python dependencies
    README.md
```

# Desktop Python version

## Requirements

Install the Python dependencies with:

```bash
python -m pip install -r requirements.txt
```

The project currently uses:

```text
pyadi-iio
pylibiio
```

On Windows the native Analog Devices libiio runtime and drivers must also be installed.

Check the installation with:

```bash
python -c "import adi; import iio; print('ADI:', adi.__version__); print('IIO:', iio.version)"
```

Check that the SDR is visible:

```bash
iio_info -S
```

For a network connected Pluto compatible device:

```bash
iio_info -u ip:192.168.2.1
```

## Run the GUI

```bash
python qrss_beacon.py
```

The default URI is:

```text
ip:192.168.2.1
```

The GUI provides RF frequency, DDS offset, TX gain, DDS amplitude, message, QRSS speed, repeat timing, a two second CW test and explicit TX stop control.

# Standalone embedded version

The standalone version is `qrss_beacon.sh`.

It runs directly on the embedded Linux system in the Zynq and writes to the AD936x PHY and FPGA DDS through sysfs. Once installed, the board can operate as a self contained QRSS transmitter using only power and an antenna or suitable RF load.

## Verify the IIO devices

SSH into the SDR and inspect the available devices:

```bash
for x in /sys/bus/iio/devices/iio:device*
do
    if [ -f "$x/name" ]; then
        echo "$x : $(cat "$x/name")"
    fi
done
```

On the tested board this returns:

```text
/sys/bus/iio/devices/iio:device0 : ad9361-phy
/sys/bus/iio/devices/iio:device1 : xadc
/sys/bus/iio/devices/iio:device2 : cf-ad9361-dds-core-lpc
/sys/bus/iio/devices/iio:device3 : cf-ad9361-lpc
```

## Install the standalone beacon

From Windows PowerShell, copy the script to the persistent JFFS2 area:

```powershell
scp -O .\qrss_beacon.sh root@192.168.2.1:/mnt/jffs2/qrss_beacon.sh
```

The capital `-O` is important with current Windows OpenSSH because many Pluto firmware images provide legacy SCP but do not include an SFTP server.

Then connect to the board:

```powershell
ssh root@192.168.2.1
```

Make the script executable:

```bash
chmod +x /mnt/jffs2/qrss_beacon.sh
```

Run it:

```bash
/mnt/jffs2/qrss_beacon.sh
```

A normal startup looks similar to:

```text
===============================================
 Zynq7010 / PlutoSDR QRSS Beacon
 Created by SV1EEX
===============================================

Initialising transmitter...

Callsign:       SV1EEX
RF frequency:   144400000 Hz
TX LO:          144300000 Hz
DDS offset:     100000 Hz
TX gain:        0.000000 dB
DDS level:      1.000000
QRSS dot:       3 seconds
Repeat gap:     30 seconds

Beacon running
Press Ctrl C to stop
```

Stop the standalone beacon with:

```text
Ctrl+C
```

The cleanup handler sets all DDS scales to zero before the script exits.

If software control is lost and the board provides a physical `RST` button, pressing `RST` reboots the SDR and terminates the current transmit state.

## Standalone configuration

The main settings are near the top of `qrss_beacon.sh`:

```bash
CALLSIGN="SV1EEX"
RF_FREQ=144400000
DDS_OFFSET=100000
TX_GAIN="0.000000"
DDS_LEVEL="1.000000"
DOT=3
REPEAT_GAP=30
```

Change these before copying the file to the SDR or edit the persistent copy directly over SSH.

# Frequency generation

The wanted RF carrier is generated as the sum of the AD936x TX local oscillator and an FPGA DDS offset.

Example:

```text
Wanted RF frequency     144.400000 MHz
DDS offset                0.100000 MHz
TX LO                   144.300000 MHz

TX LO + DDS offset = wanted RF frequency
```

Keeping the DDS tone away from zero Hz helps separate the wanted signal from LO leakage and DC related artifacts around the SDR local oscillator.

The tested FPGA image supports a 3.84 MHz DDS sample rate used by the Python implementation.

# QRSS timing

| Mode | Dot | Dash |
| --- | ---: | ---: |
| QRSS1 | 1 s | 3 s |
| QRSS3 | 3 s | 9 s |
| QRSS6 | 6 s | 18 s |
| QRSS10 | 10 s | 30 s |

The standalone shell version uses the `DOT` variable directly, so other slow CW timing values can also be selected.

# TX level

`TX_GAIN` controls the AD936x transmit attenuation. On the development board the available range is approximately:

```text
-89.75 dB to 0 dB
```

`DDS_LEVEL` controls the FPGA DDS scale, with `1.0` representing full scale at the DDS level.

These values do not directly specify output power in watts or dBm. Actual RF output depends on hardware, frequency, calibration, filtering and any external RF stages.

# Verification

An independent receiver and narrow waterfall are the easiest way to verify correct operation.

For QRSS, the transmitted carrier should appear and disappear according to the slow Morse timing. Receiver gain should be kept low enough to avoid overload when testing nearby.

# Safety and operating responsibility

This software controls an RF transmitter. The operator is responsible for selecting frequencies, power levels, identification methods and operating conditions that comply with the applicable amateur radio licence, local regulations and band plan.

Example frequencies in the source are configuration examples only.

# Project direction

The current project demonstrates both host controlled and autonomous embedded SDR transmission using the stock Analog Devices FPGA DDS.

Possible future work includes automatic startup, watchdog recovery, persistent runtime configuration, GPSDO or external reference support, frequency drift measurement, FSKCW, telemetry, browser based control and custom FPGA signal processing.

# Author

**SV1EEX**

GitHub: `z1000biker`

Repository: `z1000biker/qrssbeaconplutosdr`
