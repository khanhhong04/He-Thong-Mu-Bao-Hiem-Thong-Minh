// /app/(tabs)/index.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { HelmetStatus } from '../../components/HelmetStatus';
import { bleManager } from '../../ble/manager';
import { ImpactModal } from '../../components/impact-modal';
import { sendImpactToServer } from '../../api';

export default function Home() {
  const [connected, setConnected] = useState(false);
  const [modalData, setModalData] = useState<any>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  // 🔒 khóa sau SOS (millisecond timestamp)
  const [sosLockUntil, setSosLockUntil] = useState<number>(0);
  // 🟥 banner hiển thị trong thời gian khóa
  const [showBanner, setShowBanner] = useState<boolean>(false);

  useEffect(() => {
    // Trạng thái kết nối
    bleManager.onConnected = (ok) => {
      console.log('[UI] onConnected =', ok);
      setConnected(ok);
      if (!ok) setIsConnecting(false);
    };

    // Nhận notify từ ESP32
    bleManager.onImpact = (msg) => {
      console.log('[UI] Nhận notify từ BLE:', msg);
      const now = Date.now();

      // 1) Case IMPACT_AI (plain text "IMPACT")
      if (msg?.type === 'IMPACT_AI') {
        if (now < sosLockUntil) {
          console.log('[UI] Bỏ qua IMPACT_AI vì đang khoá sau SOS');
          return;
        }
        setModalData({
          type: 'IMPACT_AI',
          p: msg.p ?? undefined,
        });
        return;
      }

      // 2) incident từ backend
      if (now < sosLockUntil && msg?.type === 'incident_begin') {
        console.log('[UI] Bỏ qua incident_begin vì đang khoá sau SOS');
        return;
      }
      if (msg?.type === 'incident_begin') {
        setModalData(msg);
        return;
      }
      if (msg?.type === 'incident_end') {
        setModalData(null);
        return;
      }

      // 3) JSON AI từ firmware: { type: 'ai', impact: 0/1, p: ... }
      if (msg?.type === 'ai' && msg.impact === 1) {
        if (now < sosLockUntil) {
          console.log('[UI] Bỏ qua impact=1 (ai) vì đang khoá sau SOS');
          return;
        }
        setModalData(msg);
        return;
      }
    };

    return () => {
      bleManager.onImpact = null;
      bleManager.onConnected = null;
    };
  }, [sosLockUntil]); // để đọc được giá trị khóa mới nhất

  const handleConnect = async () => {
    if (connected) {
      console.log('[UI] user tapped disconnect');
      await bleManager.disconnect('ui-toggle');
      setModalData(null);
      return;
    }

    setIsConnecting(true);
    let ok = await bleManager.connect();
    if (!ok) {
      Alert.alert('Kết nối thất bại', 'Thử reset BLE và kết nối lại…');
      bleManager.reset();
      await new Promise((r) => setTimeout(r, 1200));
      ok = await bleManager.connect();
    }
    if (!ok) setIsConnecting(false);
  };

  // ====== Modal callbacks ======
  const handleACK = () => {
    console.log('[UI] User ACK');
    bleManager.sendACK();
    setModalData(null);
  };

  // KHÔNG await API trong UI, tránh kẹt modal
  const handleSOS = (ai_p?: number) => {
    console.log('[UI] User SOS');
    bleManager.sendSOS();

    // ✅ Đóng modal ngay lập tức
    setModalData(null);

    // 🔒 Khóa 2 phút
    const lockMs = 2 * 60 * 1000;
    const until = Date.now() + lockMs;
    setSosLockUntil(until);

    // 🟥 Bật banner và hẹn giờ ẩn
    setShowBanner(true);
    setTimeout(() => setShowBanner(false), lockMs);

    // ✅ Gửi lên server dạng "fire & forget"
    (async () => {
      try {
        console.log('[UI] sending impact to server...');
        await sendImpactToServer({ ai_p });
        console.log('[UI] sendImpactToServer DONE');
      } catch (e: any) {
        console.log('[UI] sendImpactToServer ERROR', e?.message || e);
        // Nếu muốn có thể mở khóa khi lỗi:
        // setSosLockUntil(0);
        // setShowBanner(false);
      }
    })();
  };

  // (tuỳ chọn) Đếm ngược hiển thị còn bao lâu hết khóa
  const remainSec = Math.max(0, Math.ceil((sosLockUntil - Date.now()) / 1000));

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Smart Helmet</Text>
      <HelmetStatus connected={connected} onConnect={handleConnect} />
      {isConnecting && <Text style={styles.connecting}>Đang quét thiết bị…</Text>}

      {/* 🟥 Banner SOS Lock */}
      {showBanner && (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>
            🚨 Đã gửi cứu hộ – Tạm khóa cảnh báo 2 phút
            {remainSec > 0 ? ` (còn ${remainSec}s)` : ''}
          </Text>
        </View>
      )}

      {/* Modal cảnh báo */}
      <ImpactModal data={modalData} onACK={handleACK} onSOS={handleSOS} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginVertical: 20 },
  connecting: { textAlign: 'center', color: '#666', marginTop: 10, fontStyle: 'italic' },

  banner: {
    backgroundColor: '#ff4d4d',
    padding: 10,
    borderRadius: 8,
    marginTop: 10,
  },
  bannerText: {
    color: '#fff',
    fontWeight: 'bold',
    textAlign: 'center',
  },
});
