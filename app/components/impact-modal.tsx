import { Modal, View, Text, Button, StyleSheet } from 'react-native';


interface Props {
  data: any;                 // JSON notify nhận từ BLE
  onACK: () => void;         // gọi khi user bấm "Tôi ổn" (UI sẽ đóng modal)
  onSOS: (ai_p?: number) => void; // gọi khi user bấm "Gửi cứu hộ"
}

export function ImpactModal({ data, onACK, onSOS }: Props) {
  // MỞ modal khi có incident_begin
   const visible =
    !!data &&
    (
      data.type === 'IMPACT_AI' ||           // 🔴 từ firmware AI logistic
      data.type === 'incident_begin' ||      // 🔵 nếu sau này backend phát sự cố
      (data.type === 'ai' && data.impact === 1) // fallback cũ
    );

  if (!visible) return null;

  const ai_p = typeof data.p === 'number' ? data.p : undefined;

  return (
    <Modal transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.modal}>
          <Text style={styles.title}>CẢNH BÁO TAI NẠN!</Text>
          {typeof ai_p === 'number' && (
            <Text>Xác suất AI: {(ai_p * 100).toFixed(1)}%</Text>
          )}
          <View style={styles.buttons}>
            <Button title="Tôi ổn" onPress={onACK} color="green" />
            <Button
              title="Gửi cứu hộ"
              onPress={() => {
                console.log('Người dùng bấm GỬI CỨU HỘ');
                onSOS(ai_p);  // để parent lo gửi BLE + HTTP + khóa 2 phút, v.v.
              }}
              color="red"
            />


          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'center', padding: 20 },
  modal: { backgroundColor: '#fff', padding: 20, borderRadius: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: 'red', marginBottom: 10 },
  buttons: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 },
});
