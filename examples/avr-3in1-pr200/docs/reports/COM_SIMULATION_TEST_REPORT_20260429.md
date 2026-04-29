# COM simulation test report for AVR_3IN1_PR200

Date: 2026-04-29

## What was simulated

The machine still exposes only one real serial API port:

- `COM1`: `Последовательный порт (COM1)`

The OWEN Logic project is configured for:

- `COM3`
- `9600 8N1`
- Modbus address `16`

`COM3` is currently disconnected/unknown in Windows, so OWEN Logic cannot open it as a real COM port.

To test the COM protocol without installing a kernel driver, I created a Python TCP null-modem pair and used pyserial `socket://` endpoints:

- test client endpoint: virtual left side
- emulator endpoint: virtual right side
- bytes are forwarded both ways exactly like a null-modem link

This verifies serial-frame behavior through a port-like transport, not by directly calling emulator functions.

## Code changed

- `owen_logic_com_emulator.py`
  - now supports pyserial URL ports such as `socket://127.0.0.1:PORT`;
  - cleanly handles serial disconnect during test shutdown.

- `test_com_emulator_virtual_port.py`
  - adds a virtual null-modem pair;
  - starts the OWEN/PR200 Modbus RTU emulator on one side;
  - sends Modbus RTU frames from a client on the other side.

## Virtual-port tests

Command:

```powershell
python -m unittest test_com_emulator_virtual_port -v
```

Result:

- Ran 7 tests
- OK

Covered through the virtual port:

- `0x11` report slave id;
- `0x03` read holding registers;
- `0x04` read input registers;
- `0x05` write single coil and read back by `0x01`;
- `0x06` write single holding register and read back by `0x03`;
- wrong slave address is ignored;
- bad CRC frame is ignored.

Log:

- `owen_logic_com_emulator_virtual_port.log`

## AVR 3-in-1 invariant tests

Command:

```powershell
python -m unittest test_avr_3in1 test_avr_3in1_invariants test_open_owen_project -v
```

Result:

- Ran 64 tests
- OK

This includes:

- scenario tests;
- exhaustive invariants;
- delay-memory safety invariants;
- proof that the currently open OWEN Logic `.owle` contains and uses the same `FB_AVR_3IN1_PR200` source as the verified local file.

## Important boundary

This proves the emulator and AVR logic under an automated virtual transport.

It does not make a Windows COM port visible to OWEN Logic. For OWEN Logic itself to connect to a simulated device, Windows must expose a real virtual COM pair, for example:

- OWEN Logic side: `COM13`
- emulator side: `COM14`

Then the emulator command would be:

```powershell
python .\owen_logic_com_emulator.py --port COM14 --address 16 --baudrate 9600
```

and OWEN Logic would be configured to open `COM13`.
