"""
===============================================================================
Zynq7010 / PlutoSDR QRSS Beacon
===============================================================================

Creator: SV1EEX

A small Tkinter GUI for slow CW / QRSS beacon transmission with PlutoSDR and
compatible Zynq7000 + AD936x SDRs exposing the Analog Devices FPGA DDS core.

Project: https://github.com/z1000biker/qrssbeaconplutosdr
===============================================================================
"""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

import adi


APP_TITLE = "Zynq7010 / PlutoSDR QRSS Beacon"
CREATOR = "SV1EEX"
VERSION = "1.0.0"

DEFAULT_URI = "ip:192.168.2.1"
DEFAULT_RF_MHZ = "144.400000"
DEFAULT_DDS_OFFSET_HZ = "100000"
DEFAULT_MESSAGE = "SV1EEX"
DEFAULT_REPEAT_GAP_S = "30"

SAMPLE_RATE = 3_840_000
TX_BANDWIDTH = 500_000
MIN_TX_GAIN_DB = -89.75
MAX_TX_GAIN_DB = 0.0

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.", "/": "-..-.",
    ".": ".-.-.-", "?": "..--..",
}

QRSS_DOT_TIMES = {
    "QRSS1": 1.0,
    "QRSS3": 3.0,
    "QRSS6": 6.0,
    "QRSS10": 10.0,
}


class QRSSBeaconGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{APP_TITLE} | Created by {CREATOR}")
        self.root.geometry("780x780")
        self.root.resizable(False, False)

        self.sdr = None
        self.connected = False
        self.busy = False
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.sdr_lock = threading.Lock()

        self._build_gui()
        self.root.protocol("WM_DELETE_WINDOW", self._close_application)

    def _build_gui(self) -> None:
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text=APP_TITLE, font=("Segoe UI", 18, "bold")).pack()
        ttk.Label(
            main,
            text=f"Created by {CREATOR}    Version {VERSION}",
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(2, 14))

        connection = ttk.LabelFrame(main, text="SDR connection", padding=12)
        connection.pack(fill="x", pady=5)

        ttk.Label(connection, text="IIO URI").grid(row=0, column=0, sticky="w")
        self.uri_var = tk.StringVar(value=DEFAULT_URI)
        ttk.Entry(connection, textvariable=self.uri_var, width=32).grid(
            row=0, column=1, padx=8
        )
        self.connect_button = ttk.Button(
            connection, text="CONNECT", command=self._connect_sdr
        )
        self.connect_button.grid(row=0, column=2, padx=5)

        rf = ttk.LabelFrame(main, text="RF settings", padding=12)
        rf.pack(fill="x", pady=5)

        ttk.Label(rf, text="RF frequency MHz").grid(row=0, column=0, sticky="w")
        self.frequency_var = tk.StringVar(value=DEFAULT_RF_MHZ)
        ttk.Entry(rf, textvariable=self.frequency_var, width=18).grid(
            row=0, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(rf, text="DDS offset Hz").grid(row=1, column=0, sticky="w")
        self.offset_var = tk.StringVar(value=DEFAULT_DDS_OFFSET_HZ)
        ttk.Entry(rf, textvariable=self.offset_var, width=18).grid(
            row=1, column=1, padx=8, pady=4, sticky="w"
        )

        ttk.Label(rf, text="TX gain dB").grid(row=2, column=0, sticky="w")
        self.gain_var = tk.DoubleVar(value=0.0)
        ttk.Scale(
            rf,
            from_=MIN_TX_GAIN_DB,
            to=MAX_TX_GAIN_DB,
            variable=self.gain_var,
            orient="horizontal",
            length=300,
            command=self._update_gain_label,
        ).grid(row=2, column=1, padx=8, pady=6)
        self.gain_label = ttk.Label(rf, text="0.00 dB")
        self.gain_label.grid(row=2, column=2, sticky="w")

        ttk.Label(rf, text="DDS amplitude").grid(row=3, column=0, sticky="w")
        self.dds_var = tk.DoubleVar(value=1.0)
        ttk.Scale(
            rf,
            from_=0.001,
            to=1.0,
            variable=self.dds_var,
            orient="horizontal",
            length=300,
            command=self._update_dds_label,
        ).grid(row=3, column=1, padx=8, pady=6)
        self.dds_label = ttk.Label(rf, text="1.000")
        self.dds_label.grid(row=3, column=2, sticky="w")

        beacon = ttk.LabelFrame(main, text="QRSS beacon", padding=12)
        beacon.pack(fill="x", pady=5)

        ttk.Label(beacon, text="Message").grid(row=0, column=0, sticky="w")
        self.message_var = tk.StringVar(value=DEFAULT_MESSAGE)
        ttk.Entry(
            beacon,
            textvariable=self.message_var,
            width=32,
            font=("Consolas", 12),
        ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(beacon, text="Mode").grid(row=1, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="QRSS3")
        ttk.Combobox(
            beacon,
            textvariable=self.mode_var,
            values=tuple(QRSS_DOT_TIMES.keys()),
            state="readonly",
            width=12,
        ).grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(beacon, text="Repeat gap seconds").grid(
            row=2, column=0, sticky="w"
        )
        self.gap_var = tk.StringVar(value=DEFAULT_REPEAT_GAP_S)
        ttk.Entry(beacon, textvariable=self.gap_var, width=12).grid(
            row=2, column=1, padx=8, pady=4, sticky="w"
        )

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=15)

        self.test_button = ttk.Button(
            buttons, text="2 SECOND CW TEST", command=self._start_test
        )
        self.test_button.pack(side="left", padx=5)

        self.start_button = ttk.Button(
            buttons, text="START BEACON", command=self._start_beacon
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            buttons, text="STOP TX", command=self._stop_tx
        )
        self.stop_button.pack(side="left", padx=5)

        status = ttk.LabelFrame(main, text="Status", padding=12)
        status.pack(fill="both", expand=True, pady=5)

        self.status_var = tk.StringVar(value="NOT CONNECTED")
        ttk.Label(
            status, textvariable=self.status_var, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 8))

        self.current_var = tk.StringVar(value="")
        ttk.Label(
            status, textvariable=self.current_var, font=("Consolas", 15, "bold")
        ).pack(anchor="w", pady=4)

        self.log = tk.Text(
            status, height=11, width=86, state="disabled", font=("Consolas", 9)
        )
        self.log.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Hardware emergency stop: press RST on the SDR",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(8, 0))

    def _update_gain_label(self, _value=None) -> None:
        self.gain_label.configure(text=f"{self.gain_var.get():.2f} dB")

    def _update_dds_label(self, _value=None) -> None:
        self.dds_label.configure(text=f"{self.dds_var.get():.3f}")

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))

    def _set_current(self, text: str) -> None:
        self.root.after(0, lambda: self.current_var.set(text))

    def _log(self, text: str) -> None:
        def write() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        self.root.after(0, write)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.root.after(0, lambda: self.test_button.configure(state=state))
        self.root.after(0, lambda: self.start_button.configure(state=state))
        self.root.after(0, lambda: self.connect_button.configure(state=state))

    def _connect_sdr(self) -> None:
        if self.busy:
            return

        try:
            uri = self.uri_var.get().strip()
            self.status_var.set("CONNECTING")
            self.root.update_idletasks()

            sdr = adi.Pluto(uri=uri)
            sdr.sample_rate = SAMPLE_RATE
            sdr.tx_rf_bandwidth = TX_BANDWIDTH
            sdr.disable_dds()

            self.sdr = sdr
            self.connected = True
            self.status_var.set("CONNECTED / TX OFF")
            self._log(f"Connected to {uri}")
            self._log(f"Sample rate: {int(self.sdr.sample_rate)} Hz")
            self._log("DDS disabled")
        except Exception as error:
            self.connected = False
            self.sdr = None
            self.status_var.set("CONNECTION FAILED")
            messagebox.showerror("Connection error", str(error))

    def _get_parameters(self) -> dict:
        rf = int(float(self.frequency_var.get()) * 1_000_000)
        offset = int(self.offset_var.get())
        gain = float(self.gain_var.get())
        dds_level = float(self.dds_var.get())
        gap = float(self.gap_var.get())
        message = self.message_var.get().strip().upper()
        mode = self.mode_var.get()

        if mode not in QRSS_DOT_TIMES:
            raise ValueError("Invalid QRSS mode")
        if not message:
            raise ValueError("Beacon message is empty")
        if offset <= 0 or offset >= SAMPLE_RATE / 2:
            raise ValueError(
                f"DDS offset must be greater than zero and below {SAMPLE_RATE // 2} Hz"
            )
        if not MIN_TX_GAIN_DB <= gain <= MAX_TX_GAIN_DB:
            raise ValueError(
                f"TX gain must be between {MIN_TX_GAIN_DB} and {MAX_TX_GAIN_DB} dB"
            )
        if not 0.0 < dds_level <= 1.0:
            raise ValueError("DDS amplitude must be greater than 0 and no more than 1")
        if gap < 0:
            raise ValueError("Repeat gap cannot be negative")

        tx_lo = rf - offset
        if tx_lo <= 0:
            raise ValueError("Invalid TX LO frequency")

        unsupported = sorted({c for c in message if c != " " and c not in MORSE})
        if unsupported:
            raise ValueError(
                "Unsupported Morse character(s): " + " ".join(unsupported)
            )

        return {
            "rf": rf,
            "offset": offset,
            "gain": gain,
            "dds_level": dds_level,
            "gap": gap,
            "message": message,
            "mode": mode,
            "dot": QRSS_DOT_TIMES[mode],
            "tx_lo": tx_lo,
        }

    def _configure_transmitter(self, p: dict) -> None:
        with self.sdr_lock:
            self.sdr.disable_dds()
            self.sdr.sample_rate = SAMPLE_RATE
            self.sdr.tx_rf_bandwidth = TX_BANDWIDTH
            self.sdr.tx_hardwaregain_chan0 = p["gain"]
            self.sdr.tx_lo = int(p["tx_lo"])

        self._log(f"TX LO: {int(self.sdr.tx_lo)} Hz")
        self._log(f"DDS offset: {p['offset']} Hz")
        self._log(f"Requested RF: {p['rf']} Hz")
        self._log(f"TX gain: {p['gain']:.2f} dB")
        self._log(f"DDS amplitude: {p['dds_level']:.3f}")

    def _key_on(self, p: dict) -> None:
        with self.sdr_lock:
            self.sdr.dds_single_tone(
                int(p["offset"]), float(p["dds_level"]), channel=0
            )

    def _key_off(self) -> None:
        if self.sdr is None:
            return
        with self.sdr_lock:
            self.sdr.disable_dds()

    def _wait(self, seconds: float) -> bool:
        return self.stop_event.wait(seconds)

    def _send_symbol(self, symbol: str, p: dict) -> bool:
        if self.stop_event.is_set():
            return False

        duration = p["dot"] if symbol == "." else p["dot"] * 3
        self._key_on(p)
        stop_requested = self._wait(duration)
        self._key_off()
        return not stop_requested

    def _send_character(self, character: str, p: dict) -> bool:
        code = MORSE[character]
        self._set_current(f"{character}     {code}")

        for index, symbol in enumerate(code):
            if not self._send_symbol(symbol, p):
                return False
            if index < len(code) - 1 and self._wait(p["dot"]):
                return False

        return True

    def _send_message(self, p: dict) -> bool:
        message = p["message"]
        index = 0

        while index < len(message):
            if self.stop_event.is_set():
                return False

            character = message[index]
            if character == " ":
                self._set_current("WORD SPACE")
                if self._wait(p["dot"] * 7):
                    return False
                index += 1
                continue

            self._log(f"{character}   {MORSE[character]}")
            if not self._send_character(character, p):
                return False

            if index + 1 < len(message) and message[index + 1] != " ":
                if self._wait(p["dot"] * 3):
                    return False

            index += 1

        return True

    def _start_beacon(self) -> None:
        if not self.connected or self.sdr is None:
            messagebox.showwarning("Not connected", "Connect to the SDR first.")
            return
        if self.busy:
            return

        try:
            p = self._get_parameters()
        except Exception as error:
            messagebox.showerror("Parameter error", str(error))
            return

        self.stop_event.clear()
        self._set_busy(True)
        self.worker_thread = threading.Thread(
            target=self._beacon_worker, args=(p,), daemon=True
        )
        self.worker_thread.start()

    def _beacon_worker(self, p: dict) -> None:
        try:
            self._configure_transmitter(p)
            self._log(f"Beacon started: {p['message']}")
            self._log(f"Mode: {p['mode']}")

            while not self.stop_event.is_set():
                self._set_status("TRANSMITTING QRSS")
                self._log(f"Sending: {p['message']}")

                if not self._send_message(p):
                    break

                self._key_off()
                self._set_current("")

                if self.stop_event.is_set():
                    break

                self._set_status(f"WAITING {p['gap']} SECONDS")
                if self._wait(p["gap"]):
                    break

        except Exception as error:
            self._log(f"ERROR: {error}")
            self._set_status("ERROR")
        finally:
            try:
                self._key_off()
            except Exception as error:
                self._log(f"DDS OFF error: {error}")
            self._set_current("")
            self._set_busy(False)
            self._set_status("CONNECTED / TX OFF")
            self._log("Beacon stopped")
            self._log("DDS disabled")

    def _start_test(self) -> None:
        if not self.connected or self.sdr is None:
            messagebox.showwarning("Not connected", "Connect to the SDR first.")
            return
        if self.busy:
            return

        try:
            p = self._get_parameters()
        except Exception as error:
            messagebox.showerror("Parameter error", str(error))
            return

        self.stop_event.clear()
        self._set_busy(True)
        self.worker_thread = threading.Thread(
            target=self._test_worker, args=(p,), daemon=True
        )
        self.worker_thread.start()

    def _test_worker(self, p: dict) -> None:
        try:
            self._configure_transmitter(p)
            self._set_status("CW TEST TRANSMITTING")
            self._log(f"2 second carrier at {p['rf']} Hz")
            self._key_on(p)
            self._wait(2.0)
        except Exception as error:
            self._log(f"ERROR: {error}")
            self._set_status("ERROR")
        finally:
            try:
                self._key_off()
            except Exception as error:
                self._log(f"DDS OFF error: {error}")
            self._set_busy(False)
            self._set_current("")
            self._set_status("CONNECTED / TX OFF")
            self._log("CW test finished")
            self._log("DDS disabled")

    def _stop_tx(self) -> None:
        if not self.connected:
            self.status_var.set("NOT CONNECTED")
            return

        if self.busy:
            self.stop_event.set()
            self.status_var.set("STOP REQUESTED")
            self._log("STOP requested")
            return

        try:
            self._key_off()
            self.status_var.set("CONNECTED / TX OFF")
            self._log("TX already stopped")
            self._log("DDS disabled")
        except Exception as error:
            self.status_var.set("TX OFF ERROR")
            self._log(f"DDS OFF error: {error}")

    def _close_application(self) -> None:
        self.stop_event.set()

        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=3.0)

        if self.sdr is not None and not (
            self.worker_thread is not None and self.worker_thread.is_alive()
        ):
            try:
                self._key_off()
            except Exception:
                pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    QRSSBeaconGUI(root)
    root.mainloop()
