import asyncio
import argparse
import csv
from pathlib import Path
from bleak import BleakClient, BleakScanner

# UUID Nordic UART (giống firmware)
UUID_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UUID_CHAR_NOTIFY = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
UUID_CHAR_WRITE  = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# ====== TẦN SỐ LẤY MẪU TƯƠNG ỨNG FIRMWARE ======
SAMPLE_RATE_HZ = 1000
SAMPLE_PERIOD_MS = 1000 / SAMPLE_RATE_HZ  # 1 ms

def decode_sample(payload: bytes, index: int, label: int | None):
    """
    Firmware hiện tại: mỗi notify = 1 sample, 13 byte:
      ax,ay,az,gx,gy,gz: int16 LE x6 (12B)
      marker:            uint8       (1B)
    Không còn header seq / t0_ms / N.

    Ta tự tạo:
      idx    = số thứ tự mẫu (0,1,2,...)
      t_ms   = idx * SAMPLE_PERIOD_MS
    """
    if len(payload) != 13:
        # nếu vì lý do gì đó không phải 13 byte thì bỏ qua
        return None

    ax = int.from_bytes(payload[0:2], "little", signed=True)
    ay = int.from_bytes(payload[2:4], "little", signed=True)
    az = int.from_bytes(payload[4:6], "little", signed=True)
    gx = int.from_bytes(payload[6:8], "little", signed=True)
    gy = int.from_bytes(payload[8:10], "little", signed=True)
    gz = int.from_bytes(payload[10:12], "little", signed=True)
    marker = payload[12]

    t_ms = int(index * SAMPLE_PERIOD_MS)

    return {
        "idx":    index,
        "t_ms":   t_ms,
        "ax_raw": ax,
        "ay_raw": ay,
        "az_raw": az,
        "gx_raw": gx,
        "gy_raw": gy,
        "gz_raw": gz,
        "marker": marker,
        "label":  label if label is not None else ""
    }

async def find_device(name: str | None, address: str | None, timeout=6.0):
    """Tìm thiết bị BLE theo name hoặc address."""
    if address:
        return address
    print(f"Scanning for device named '{name}' ...")
    devices = await BleakScanner.discover(timeout=timeout)
    for d in devices:
        if (d.name or "").strip() == (name or "").strip():
            print(f"Found {name} at {d.address}")
            return d.address
    raise RuntimeError(f"Device '{name}' not found. Try --address or re-scan.")

async def run(args):
    addr = await find_device(args.name, args.address)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {addr} ...")
    async with BleakClient(addr) as client:
        if not client.is_connected:
            raise RuntimeError("BLE connect failed")
        print("Connected.")

        rows_buffer = []
        total_samples = 0
        sample_index = 0  # idx tăng dần

        def handle_notify(_, data: bytearray):
            nonlocal rows_buffer, total_samples, sample_index
            row = decode_sample(bytes(data), sample_index, args.label)
            if row:
                rows_buffer.append(row)
                sample_index += 1
                total_samples += 1

        await client.start_notify(UUID_CHAR_NOTIFY, handle_notify)
        print("Notify enabled.")

        # Gửi START (nếu firmware dùng START/STOP)
        try:
            await client.write_gatt_char(UUID_CHAR_WRITE, b"START")
            print("START sent. Logging...")
        except Exception as e:
            print(f"Cannot send START (ignore if not used in firmware): {e}")

        fieldnames = [
            "idx", "t_ms",
            "ax_raw","ay_raw","az_raw",
            "gx_raw","gy_raw","gz_raw",
            "marker","label"
        ]

        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            end_time = None
            if args.seconds > 0:
                end_time = asyncio.get_event_loop().time() + args.seconds

            try:
                last_flush = 0.0
                while True:
                    await asyncio.sleep(0.2)
                    now = asyncio.get_event_loop().time()

                    # flush buffer mỗi 0.5s
                    if now - last_flush > 0.5 and rows_buffer:
                        writer.writerows(rows_buffer)
                        f.flush()
                        rows_buffer.clear()
                        last_flush = now

                    if end_time and now >= end_time:
                        break

            except KeyboardInterrupt:
                print("Interrupted by user.")

        # Gửi STOP & tắt notify
        try:
            await client.write_gatt_char(UUID_CHAR_WRITE, b"STOP")
            print("STOP sent.")
        except Exception:
            pass

        await client.stop_notify(UUID_CHAR_NOTIFY)
        print(f"Saved samples to: {out_path} (total samples ~ {total_samples})")

def parse_args():
    p = argparse.ArgumentParser(description="SmartHelmet BLE → CSV logger (1kHz)")
    p.add_argument("--name", default="SmartHelmet",
                   help="BLE device name (default: SmartHelmet)")
    p.add_argument("--address",
                   help="BLE MAC address (if you prefer connecting by address)")
    p.add_argument("--out", required=True,
                   help="Output CSV path (e.g. E:\\smart-helmet\\data_logger\\session_1.csv)")
    p.add_argument("--seconds", type=int, default=20,
                   help="Duration to record (seconds). 0 = until Ctrl+C")
    p.add_argument("--label", type=int, choices=[0, 1],
                   help="Label cho toàn bộ file: 0=noimpact, 1=impact (tạm dùng nếu muốn)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(args))
