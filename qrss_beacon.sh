#!/bin/sh

###############################################################################
# Zynq7010 / PlutoSDR Standalone QRSS Beacon
#
# Creator: SV1EEX
#
# Standalone QRSS CW beacon for PlutoSDR compatible Zynq7000 and AD936x SDRs.
# Runs directly on the embedded Linux system.
#
# No host computer is required after startup.
###############################################################################

PHY="/sys/bus/iio/devices/iio:device0"
DDS="/sys/bus/iio/devices/iio:device2"

CALLSIGN="SV1EEX"

RF_FREQ=144400000
DDS_OFFSET=100000

TX_GAIN="0.000000"
DDS_LEVEL="1.000000"

DOT=3
REPEAT_GAP=30


###############################################################################
# SYSFS FILES
###############################################################################

TX_LO="$PHY/out_altvoltage1_TX_LO_frequency"
TX_GAIN_FILE="$PHY/out_voltage0_hardwaregain"

I_FREQ="$DDS/out_altvoltage0_TX1_I_F1_frequency"
I_PHASE="$DDS/out_altvoltage0_TX1_I_F1_phase"
I_RAW="$DDS/out_altvoltage0_TX1_I_F1_raw"
I_SCALE="$DDS/out_altvoltage0_TX1_I_F1_scale"

Q_FREQ="$DDS/out_altvoltage2_TX1_Q_F1_frequency"
Q_PHASE="$DDS/out_altvoltage2_TX1_Q_F1_phase"
Q_RAW="$DDS/out_altvoltage2_TX1_Q_F1_raw"
Q_SCALE="$DDS/out_altvoltage2_TX1_Q_F1_scale"

I2_SCALE="$DDS/out_altvoltage1_TX1_I_F2_scale"
Q2_SCALE="$DDS/out_altvoltage3_TX1_Q_F2_scale"


###############################################################################
# CALCULATED FREQUENCY
###############################################################################

TX_LO_FREQ=$((RF_FREQ - DDS_OFFSET))


###############################################################################
# DDS OFF
###############################################################################

dds_off()
{
    echo "0.000000" > "$I_SCALE"
    echo "0.000000" > "$Q_SCALE"

    echo "0.000000" > "$I2_SCALE"
    echo "0.000000" > "$Q2_SCALE"
}


###############################################################################
# DDS ON
###############################################################################

dds_on()
{
    echo "$DDS_LEVEL" > "$I_SCALE"
    echo "$DDS_LEVEL" > "$Q_SCALE"
}


###############################################################################
# EMERGENCY CLEANUP
###############################################################################

cleanup()
{
    echo
    echo "Stopping transmission..."

    dds_off

    echo "DDS OFF"
    echo "Beacon stopped"

    exit 0
}


trap cleanup INT TERM HUP


###############################################################################
# INITIALISE TRANSMITTER
###############################################################################

init_tx()
{
    echo
    echo "==============================================="
    echo " Zynq7010 / PlutoSDR QRSS Beacon"
    echo " Created by SV1EEX"
    echo "==============================================="
    echo

    echo "Initialising transmitter..."

    dds_off

    echo "$TX_GAIN" > "$TX_GAIN_FILE"

    echo "$TX_LO_FREQ" > "$TX_LO"

    echo "$DDS_OFFSET" > "$I_FREQ"
    echo "$DDS_OFFSET" > "$Q_FREQ"

    echo "90000" > "$I_PHASE"
    echo "0" > "$Q_PHASE"

    echo "1" > "$I_RAW"
    echo "1" > "$Q_RAW"

    echo "0.000000" > "$I2_SCALE"
    echo "0.000000" > "$Q2_SCALE"

    echo
    echo "Callsign:       $CALLSIGN"
    echo "RF frequency:   $RF_FREQ Hz"
    echo "TX LO:          $TX_LO_FREQ Hz"
    echo "DDS offset:     $DDS_OFFSET Hz"
    echo "TX gain:        $TX_GAIN dB"
    echo "DDS level:      $DDS_LEVEL"
    echo "QRSS dot:       $DOT seconds"
    echo "Repeat gap:     $REPEAT_GAP seconds"
    echo
}


###############################################################################
# KEYING
###############################################################################

dit()
{
    printf "."

    dds_on
    sleep "$DOT"
    dds_off

    sleep "$DOT"
}


dah()
{
    printf "_"

    dds_on

    DASH=$((DOT * 3))

    sleep "$DASH"

    dds_off

    sleep "$DOT"
}


###############################################################################
# CHARACTER SPACE
###############################################################################

char_space()
{
    EXTRA=$((DOT * 2))
    sleep "$EXTRA"
}


###############################################################################
# WORD SPACE
###############################################################################

word_space()
{
    EXTRA=$((DOT * 6))
    sleep "$EXTRA"
}


###############################################################################
# MORSE CHARACTER
###############################################################################

send_char()
{
    case "$1" in

        A) dit; dah ;;
        B) dah; dit; dit; dit ;;
        C) dah; dit; dah; dit ;;
        D) dah; dit; dit ;;
        E) dit ;;
        F) dit; dit; dah; dit ;;
        G) dah; dah; dit ;;
        H) dit; dit; dit; dit ;;
        I) dit; dit ;;
        J) dit; dah; dah; dah ;;
        K) dah; dit; dah ;;
        L) dit; dah; dit; dit ;;
        M) dah; dah ;;
        N) dah; dit ;;
        O) dah; dah; dah ;;
        P) dit; dah; dah; dit ;;
        Q) dah; dah; dit; dah ;;
        R) dit; dah; dit ;;
        S) dit; dit; dit ;;
        T) dah ;;
        U) dit; dit; dah ;;
        V) dit; dit; dit; dah ;;
        W) dit; dah; dah ;;
        X) dah; dit; dit; dah ;;
        Y) dah; dit; dah; dah ;;
        Z) dah; dah; dit; dit ;;

        0) dah; dah; dah; dah; dah ;;
        1) dit; dah; dah; dah; dah ;;
        2) dit; dit; dah; dah; dah ;;
        3) dit; dit; dit; dah; dah ;;
        4) dit; dit; dit; dit; dah ;;
        5) dit; dit; dit; dit; dit ;;
        6) dah; dit; dit; dit; dit ;;
        7) dah; dah; dit; dit; dit ;;
        8) dah; dah; dah; dit; dit ;;
        9) dah; dah; dah; dah; dit ;;

        "/") dah; dit; dit; dah; dit ;;

        " ") word_space ;;

    esac
}


###############################################################################
# SEND MESSAGE
###############################################################################

send_message()
{
    MESSAGE="$1"

    LENGTH=${#MESSAGE}

    INDEX=1

    while [ "$INDEX" -le "$LENGTH" ]
    do

        CHARACTER=$(printf "%s" "$MESSAGE" | cut -c "$INDEX")

        printf "%s " "$CHARACTER"

        send_char "$CHARACTER"

        if [ "$CHARACTER" != " " ]
        then
            char_space
        fi

        INDEX=$((INDEX + 1))

    done

    echo
}


###############################################################################
# MAIN
###############################################################################

init_tx

echo "Beacon running"
echo "Press Ctrl C to stop"
echo

while true
do

    echo "Sending $CALLSIGN"

    send_message "$CALLSIGN"

    dds_off

    echo
    echo "Waiting $REPEAT_GAP seconds"
    echo

    sleep "$REPEAT_GAP"

done
