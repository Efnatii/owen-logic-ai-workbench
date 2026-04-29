# COM test report for AVR_3IN1_PR200

Date: 2026-04-29

## OWEN Logic connection settings found

From `C:\Users\Alexandra\AppData\Roaming\OWEN\OWEN Logic\config.xml`:

- Port: `COM3`
- Baud rate: `9600`
- Data bits: `8`
- Parity: `None`
- Stop bits: `1`
- Device address: `16`
- Connection type: `SerialPort`

## Windows COM ports currently available

Active serial ports reported by Windows/pyserial:

- `COM1`: `Последовательный порт (COM1)`

Historical/disconnected ports visible in Device Manager include `COM3`, `COM4`, `COM5`, `COM6`, `COM7`, `COM8`, `COM9`, `COM10`, but their PnP status is `Unknown`, and they are not available through the serial API.

## Read-only probe

Probe file with raw TX/RX frames:

- `COM_PROBE_20260429.txt`

Commands sent were read-only Modbus RTU requests only:

- report slave id, function `0x11`
- read device identification, function `0x2B/0x0E`
- read holding register, function `0x03`
- read input register, function `0x04`
- read coils, function `0x01`
- read discrete inputs, function `0x02`

Results:

- `COM1` opens at `9600 8N1`, slave `16`, but all read-only requests timed out.
- `COM3` fails to open: Windows reports that the port does not exist.

## Conclusion

The controller cannot currently be tested through the configured OWEN Logic COM port because `COM3` is not present in Windows. The only active port, `COM1`, does not respond to read-only Modbus probes with the configured address `16`.

Next physical/OS checks:

- Plug in or power the USB-RS485/COM adapter used as `COM3`.
- Confirm Device Manager shows the adapter as `OK`, not `Unknown`.
- Confirm OWEN Logic uses the actual present port, or update the port in OWEN Logic.
- After the port appears, repeat the COM probe with `COM3`, `9600 8N1`, address `16`.
