import asyncio
from bleak import BleakScanner

async def main():
    print("Scanning BLE devices for 5 seconds...")
    devices = await BleakScanner.discover(timeout=5.0)
    for d in devices:
        print(f"{d.name or '(no name)'}  |  {d.address}")

asyncio.run(main())
