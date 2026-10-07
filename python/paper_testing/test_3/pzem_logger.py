"""Log bus voltage/current/power from a Peacefair PZEM-003 (DC, 10 A, built-in shunt).

Why this exists
---------------
Cost of transport (paper section 2.3.3) needs the electrical energy drawn from
the supply, E = integral of V(t)*I(t) dt.  The drivers' own current telemetry
cannot give it (see CLAUDE.md: it is phase-current magnitude with no duty term),
so the bus is measured directly, inline, with this meter.  With a battery the
voltage is no longer constant, which is why V is logged alongside I.

Wiring:   battery(-) -> PZEM shunt -> robot(-)     (series, on the NEGATIVE lead)
Serial:   9600 baud, 8 data bits, NO parity, 2 STOP BITS (8N2 - the usual trap)
Protocol: Modbus RTU, slave address 1, function 0x04, registers 0x0000..0x0007
          V 0.01 V | I 0.01 A | P 0.1 W (lo,hi) | energy 1 Wh (lo,hi) | alarms
The meter's energy register has 1 Wh resolution, useless over a 20 s run, so
the logger records V/I/P samples and evaluate_capability_runs.py integrates.

Usage
-----
    python pzem_logger.py --port COM5                 # log until Ctrl-C
    python pzem_logger.py --port COM5 --interval 0.25 # poll faster to measure the refresh rate
    python pzem_logger.py --simulate --sim-seconds 60 # no hardware: synthetic file

Output: output/log/pzem_YYYYmmdd_HHMMSS.csv with columns
    t_unix, time, v_V, i_A, p_W, e_Wh, changed
`changed` is 1 when any reading differs from the previous poll; the summary at
exit uses it to report the meter's real internal refresh rate.
"""
import argparse
import csv
import math
import os
import struct
import sys
import time
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'log')


# ── Modbus RTU ───────────────────────────────────────────────────────────────

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def read_request(addr: int, start: int = 0x0000, count: int = 8) -> bytes:
    body = struct.pack('>BBHH', addr, 0x04, start, count)
    return body + struct.pack('<H', crc16(body))          # CRC low byte first


def parse_response(frame: bytes, addr: int, count: int = 8):
    """Return (V, I, P, E_Wh) or raise ValueError with the reason."""
    need = 3 + 2 * count + 2
    if len(frame) < need:
        raise ValueError('short frame (%d of %d bytes)' % (len(frame), need))
    frame = frame[:need]
    if frame[0] != addr:
        raise ValueError('address %d != %d' % (frame[0], addr))
    if frame[1] & 0x80:
        raise ValueError('modbus exception 0x%02X' % frame[2])
    if frame[1] != 0x04 or frame[2] != 2 * count:
        raise ValueError('unexpected header %02X %02X' % (frame[1], frame[2]))
    if struct.unpack('<H', frame[-2:])[0] != crc16(frame[:-2]):
        raise ValueError('CRC mismatch')
    regs = struct.unpack('>%dH' % count, frame[3:3 + 2 * count])
    v = regs[0] / 100.0
    i = regs[1] / 100.0
    p = ((regs[3] << 16) | regs[2]) / 10.0
    e = (regs[5] << 16) | regs[4]
    return v, i, p, e


class Pzem:
    def __init__(self, port: str, baud: int = 9600, addr: int = 1, timeout: float = 0.5):
        import serial                                       # pyserial
        self.addr = addr
        self.ser = serial.Serial(port, baudrate=baud, bytesize=8, parity='N',
                                 stopbits=2, timeout=timeout)

    def read(self):
        self.ser.reset_input_buffer()
        self.ser.write(read_request(self.addr))
        frame = self.ser.read(3 + 16 + 2)
        return parse_response(frame, self.addr)

    def close(self):
        self.ser.close()


class SimulatedPzem:
    """A 12 V battery under a trotting robot, refreshed once a second."""

    def __init__(self, t0: float):
        self.t0 = t0
        self.last_tick = None
        self.cache = (12.8, 0.0, 0.0, 0)

    def read(self):
        t = time.time() - self.t0
        tick = int(t)
        if tick != self.last_tick:                          # 1 Hz internal refresh
            self.last_tick = tick
            walking = (tick % 40) >= 8                      # 8 s idle, 32 s walking
            v = 12.8 - 0.25 * (t / 600.0) + 0.02 * math.sin(t)
            if walking:
                i = 1.6 + 0.35 * math.sin(2 * math.pi * 2.3 * t) + 0.05 * math.sin(7 * t)
            else:
                i = 0.35 + 0.02 * math.sin(3 * t)
            i = max(i, 0.0)
            self.cache = (round(v, 2), round(i, 2), round(v * i, 1), int(v * i * t / 3600))
        return self.cache

    def close(self):
        pass


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--port', help='serial port of the USB-TTL/RS485 adapter, e.g. COM5')
    ap.add_argument('--baud', type=int, default=9600)
    ap.add_argument('--addr', type=int, default=1)
    ap.add_argument('--interval', type=float, default=0.5,
                    help='poll period in seconds (default 0.5; the meter refreshes ~1 Hz)')
    ap.add_argument('--out', help='CSV path (default output/log/pzem_<timestamp>.csv)')
    ap.add_argument('--simulate', action='store_true', help='no hardware: synthetic readings')
    ap.add_argument('--sim-seconds', type=float, default=60.0)
    ap.add_argument('--sim-start', help='backdate a simulated file to this local time, YYYYmmdd_HHMMSS')
    args = ap.parse_args()

    if not args.simulate and not args.port:
        ap.error('--port is required (or use --simulate)')

    os.makedirs(LOG_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if args.simulate and args.sim_start:
        stamp = args.sim_start
    out = args.out or os.path.join(LOG_DIR, 'pzem_%s%s.csv' % (stamp, '_sim' if args.simulate else ''))

    if args.simulate:
        t0 = time.time()
        offset = 0.0
        if args.sim_start:
            offset = time.mktime(time.strptime(args.sim_start, '%Y%m%d_%H%M%S')) - t0
        meter = SimulatedPzem(t0)
        print('SIMULATED meter -> %s' % out)
    else:
        offset = 0.0
        meter = Pzem(args.port, args.baud, args.addr)
        print('PZEM-003 on %s (%d 8N2, addr %d) -> %s' % (args.port, args.baud, args.addr, out))
    print('Ctrl-C to stop.')

    n_polls = n_changed = n_err = 0
    prev = None
    t_start = time.time()
    t_first_change = t_last_change = None
    try:
        with open(out, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['t_unix', 'time', 'v_V', 'i_A', 'p_W', 'e_Wh', 'changed'])
            while True:
                t_poll = time.time()
                try:
                    v, i, p, e = meter.read()
                except Exception as exc:                        # noqa: BLE001 - keep logging
                    n_err += 1
                    print('\n  read error: %s' % exc)
                    time.sleep(args.interval)
                    continue
                n_polls += 1
                changed = int((v, i, p, e) != prev)
                prev = (v, i, p, e)
                if changed:
                    n_changed += 1
                    t_last_change = t_poll
                    if t_first_change is None:
                        t_first_change = t_poll
                t_unix = t_poll + offset
                w.writerow(['%.3f' % t_unix,
                            datetime.fromtimestamp(t_unix).strftime('%H:%M:%S.%f')[:-3],
                            '%.2f' % v, '%.2f' % i, '%.1f' % p, e, changed])
                fh.flush()
                print('\r  %7.2f V  %5.2f A  %6.1f W   polls %d  changed %d  errors %d'
                      % (v, i, p, n_polls, n_changed, n_err), end='', flush=True)
                if args.simulate and (t_poll - t_start) >= args.sim_seconds:
                    break
                time.sleep(max(0.0, args.interval - (time.time() - t_poll)))
    except KeyboardInterrupt:
        pass
    finally:
        meter.close()

    print('\n\nwrote %s' % out)
    print('  %d polls over %.1f s, %d errors' % (n_polls, time.time() - t_start, n_err))
    if n_changed > 1 and t_last_change > t_first_change:
        rate = (n_changed - 1) / (t_last_change - t_first_change)
        print('  meter refresh rate ~ %.2f Hz (from %d distinct readings)' % (rate, n_changed))
        if args.interval >= 1.0 / max(rate, 1e-9):
            print('  note: poll interval >= refresh period; use --interval 0.25 to measure it properly')


if __name__ == '__main__':
    main()
