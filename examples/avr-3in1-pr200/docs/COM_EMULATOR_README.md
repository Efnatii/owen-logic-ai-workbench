# OWEN Logic COM emulator

This folder contains `owen_logic_com_emulator.py`, a safe Modbus RTU slave emulator for OWEN Logic connection experiments.

## Why a virtual COM pair is required

OWEN Logic is a serial master. The emulator must be the serial slave. Two programs cannot open the same single COM port at once, so Windows needs a virtual null-modem pair:

- OWEN Logic opens one side, for example `COM13`.
- The emulator opens the paired side, for example `COM14`.

The current machine only exposes `COM1` as an active serial API port. OWEN Logic is configured for `COM3`, but `COM3` is currently a disconnected/unknown device and cannot be opened.

## Recommended setup

Create a virtual null-modem pair with a driver such as com0com:

- pair A: `COM13`
- pair B: `COM14`

Then:

1. Set OWEN Logic connection port to `COM13`.
2. Start the emulator on `COM14`:

```powershell
cd C:\__SELF_PC__\AVR_3IN1_PR200
python .\owen_logic_com_emulator.py --port COM14 --address 16 --baudrate 9600
```

3. In OWEN Logic, try connecting to the device.
4. Inspect the log:

```powershell
Get-Content .\owen_logic_com_emulator.log -Tail 50
```

## Safety

The emulator does not control real outputs. Modbus write functions update only the emulator's in-memory coils/registers. To reject writes entirely, start it with:

```powershell
python .\owen_logic_com_emulator.py --port COM14 --address 16 --baudrate 9600 --read-only-writes
```

For OWEN Logic connection handshakes, allowing in-memory writes is usually more useful and still safe because no hardware is attached.
