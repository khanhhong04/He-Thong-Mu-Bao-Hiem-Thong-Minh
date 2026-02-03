// ble/manager.ts
import { BleManager, Device, Subscription, State } from 'react-native-ble-plx';

import { Alert, Platform } from 'react-native';

const UUIDS = {
  SERVICE: '6E400001-B5A3-F393-E0A9-E50E24DCCA9E',
  NOTIFY:  '6E400003-B5A3-F393-E0A9-E50E24DCCA9E',
  WRITE:   '6E400002-B5A3-F393-E0A9-E50E24DCCA9E',
};

const log = (...a: any[]) => console.log('[BLE]', ...a);
const err = (...a: any[]) => console.log('[BLE][ERR]', ...a);

function withTimeout<T>(p: Promise<T>, ms: number, label = 'op'): Promise<T> {
  let t: any;
  return Promise.race([
    p.finally(() => clearTimeout(t)),
    new Promise<T>((_, rej) => {
      t = setTimeout(() => rej(new Error(`timeout ${label} after ${ms}ms`)), ms);
    }),
  ]) as Promise<T>;
}

async function isActuallyConnected(dev?: Device | null): Promise<boolean> {
  try { return !!(dev && (await dev.isConnected())); } catch { return false; }
}

export class BLEManager {
  manager = new BleManager();
  device: Device | null = null;

  // Subscriptions & state
  notifySub: Subscription | null = null;
  disconnectSub: Subscription | null = null;
  stateSub: Subscription | null = null;

  isScanning = false;
  scanTimeout: NodeJS.Timeout | null = null;

  onImpact: ((data: any) => void) | null = null;
  onConnected: ((connected: boolean) => void) | null = null;

  private buffer = '';
  private destroyed = false;
  private userDisconnecting = false;

  // 🔑 transactionId cho stream notify (bắt buộc để hủy an toàn)
  private notifyTxnId: string | null = null;

  constructor() {
    this.stateSub = this.manager.onStateChange((s) => {
      log('State =', s);
      if (s !== State.PoweredOn) {
        this.stopScan();
        Alert.alert('Bluetooth tắt', 'Vui lòng bật lại Bluetooth');
      }
    }, true);
  }

  private async ensureBleOn(): Promise<boolean> {
    const s = await this.manager.state();
    if (s !== State.PoweredOn) {
      Alert.alert('Bluetooth chưa bật', 'Hãy bật Bluetooth để kết nối.');
      return false;
    }
    return true;
  }

  async connect(): Promise<boolean> {
    if (this.destroyed) {
      this.manager = new BleManager();
      this.destroyed = false;
      this.stateSub = this.manager.onStateChange((s) => log('State =', s), true);
    }
    if (!(await this.ensureBleOn())) return false;

    await this.disconnect('pre-scan');

    log('Bắt đầu quét SmartHelmet...');
    this.isScanning = true;

    return new Promise<boolean>((resolve) => {
      this.scanTimeout = setTimeout(() => {
        this.stopScan();
        log('Quét tự dừng sau 10s');
        resolve(false);
      }, 10000);

      this.manager.startDeviceScan([UUIDS.SERVICE], null, (e, d) => {
        if (e) {
          err('scan', e.message);
          this.stopScan();
          resolve(false);
          return;
        }
        if (!d?.name?.includes?.('SmartHelmet')) return;

        log(`Tìm thấy: ${d.name} (${d.id})`);
        this.stopScan();
        this.connectToDevice(d).then(resolve);
      });
    });
  }

  private async connectToDevice(device: Device): Promise<boolean> {
    try {
      const d1 = await withTimeout(device.connect(), 6000, 'connect');
      const d2 = await withTimeout(d1.discoverAllServicesAndCharacteristics(), 6000, 'discover');
      this.device = d2;

      // Lắng nghe native disconnect
      this.disconnectSub?.remove?.();
      this.disconnectSub = this.manager.onDeviceDisconnected(this.device.id, (errDev, dev) => {
        log('onDeviceDisconnected', dev?.id, errDev?.message ?? '');
        if (this.userDisconnecting) {
          log('ignore native disconnect (userDisconnecting=true)');
          return;
        }
        this.cleanupNotifyOnly(); // đã hủy transaction ở nhánh user rồi
        this.device = null;
        this.onConnected?.(false);
      });

      // MTU
      try {
        if (Platform.OS === 'android') {
          await this.device.requestMTU(185);
          log('✅ MTU set to 185');
        }
      } catch (e: any) {
        log('requestMTU skip/iOS:', e?.message);
      }

      log('Kết nối thành công → setup notify');
      this.setupNotify();
      this.onConnected?.(true);
      return true;
    } catch (e: any) {
      err('connectToDevice', e?.message || e);
      this.device = null;
      this.onConnected?.(false);
      return false;
    }
  }

 
    // ========= NOTIFY =========
  private setupNotify() {
    if (!this.device) return;

    this.notifyTxnId = `notif_${this.device.id}`;

    log('Bắt đầu lắng nghe Notify...');
    this.notifySub?.remove?.();

    this.notifySub = this.device.monitorCharacteristicForService(
      UUIDS.SERVICE,
      UUIDS.NOTIFY,
      (e, ch) => {
        if (e) {
          err('notify error', e.message);
          return;
        }
        if (!ch?.value) return;

        const base64 = ch.value.trim();

        try {
          const text = atob(base64);   // ví dụ: "IMPACT\n"
          const msg = text.trim();     // "IMPACT"
          log('Text decoded:', JSON.stringify(msg));

          // 🔴 Case 1: firmware gửi "IMPACT\n"
          if (msg === 'IMPACT') {
            // bắn event lên UI
            this.onImpact?.({ type: 'IMPACT_AI' });
            return;
          }

          // 🔵 Case 2: nếu sau này đổi sang gửi JSON (giữ cho tương lai)
          if (msg.startsWith('{')) {
            try {
              const data = JSON.parse(msg);
              log('JSON from fw:', data);
              this.onImpact?.(data);
            } catch (ex: any) {
              err('parse JSON', ex?.message);
            }
          }
        } catch (ex: any) {
          err('decode base64', ex?.message);
        }
      },
      this.notifyTxnId
    );
  }


  // ========= DISCONNECT =========
  private cleanupNotifyOnly() {
    // 1) Hủy transaction trước (QUAN TRỌNG để tránh NPE trong native)
    if (this.notifyTxnId) {
      try {
        this.manager.cancelTransaction(this.notifyTxnId);
        log('cancelTransaction notifyTxnId=', this.notifyTxnId);
      } catch (e: any) {
        err('cancelTransaction', e?.message);
      }
    }

    // 2) Gỡ subscription JS
    try {
      if (this.notifySub) {
        this.notifySub.remove();
        log('notifySub removed');
      }
    } catch (e: any) {
      err('notifySub.remove', e?.message);
    } finally {
      this.notifySub = null;
      this.notifyTxnId = null;
      this.buffer = '';
    }
  }

  private async cancelNativeConnection(id: string) {
    try {
      if (this.device?.id === id && (await isActuallyConnected(this.device))) {
        if (typeof (this.device as any).cancelConnection === 'function') {
          await withTimeout((this.device as any).cancelConnection(), 3000, 'device.cancelConnection');
          log('device.cancelConnection done');
          return;
        }
      }
    } catch (e: any) {
      log('device.cancelConnection skip:', e?.message);
    }
    try {
      await withTimeout(this.manager.cancelDeviceConnection(id), 3000, 'manager.cancelDeviceConnection');
      log('manager.cancelDeviceConnection done');
    } catch (e: any) {
      log('manager.cancelDeviceConnection skip:', e?.message);
    }
  }

  async disconnect(reason: 'ui-toggle' | 'pre-scan' | 'reset' = 'ui-toggle') {
    log('disconnect() start, reason=' + reason, 'dev=' + (this.device?.id ?? '-'));
    this.userDisconnecting = true;

    const devRef = this.device;
    let ended = false;
    const endSafely = () => {
      if (ended) return;
      ended = true;

      // đã hủy transaction & notify trong cleanupNotifyOnly()
      this.stopScan();
      this.device = null;
      this.onConnected?.(false);
      this.userDisconnecting = false;
      log('disconnect() end');
    };

    // Hủy stream trước khi đụng đến native
    this.cleanupNotifyOnly();

    const watchdog = setTimeout(() => {
      log('[WD] force end after 4s');
      endSafely();
    }, 4000);

    try {
      if (await isActuallyConnected(devRef)) {
        await this.cancelNativeConnection(devRef!.id);
      } else {
        log('native already disconnected');
      }
    } catch (e: any) {
      err('disconnect main', e?.message || e);
    } finally {
      clearTimeout(watchdog);
      endSafely();
    }
  }

  stopScan() {
    if (this.isScanning) {
      this.manager.stopDeviceScan();
      this.isScanning = false;
      log('Đã dừng quét');
    }
    if (this.scanTimeout) {
      clearTimeout(this.scanTimeout);
      this.scanTimeout = null;
    }
  }

  sendACK() {
    if (!this.device) return;
    const payload = btoa('ACK');
    this.device
      .writeCharacteristicWithResponseForService(UUIDS.SERVICE, UUIDS.WRITE, payload)
      .then(() => log('ACK sent'))
      .catch((e) => err('ACK write', e?.message));
  }
    sendSOS() {
    if (!this.device) return;
    const payload = btoa('SOS');
    this.device
      .writeCharacteristicWithResponseForService(UUIDS.SERVICE, UUIDS.WRITE, payload)
      .then(() => log('SOS sent'))
      .catch((e) => err('SOS write', e?.message));
  }


  reset() {
    log('reset()');
    this.disconnect('reset').finally(() => {
      try { this.stateSub?.remove?.(); } catch {}
      try { this.manager.destroy(); } catch {}
      this.manager = new BleManager();
      this.destroyed = false;
      this.stateSub = this.manager.onStateChange((s) => log('State =', s), true);
      log('reset() done');
    });
  }

  destroy() {
    log('destroy()');
    this.disconnect('reset').finally(() => {
      try { this.stateSub?.remove?.(); } catch {}
      try { this.manager.destroy(); } catch {}
      this.destroyed = true;
      log('destroy() done');
    });
  }
}

export const bleManager = new BLEManager();
