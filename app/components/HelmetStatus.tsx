// app/components/HelmetStatus.tsx
import { View, Text, Button, StyleSheet } from 'react-native';

interface Props {
  connected: boolean;
  onConnect: () => void;
}

export function HelmetStatus({ connected, onConnect }: Props) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>Trạng thái mũ:</Text>
      <Text style={[styles.status, connected ? styles.connected : styles.disconnected]}>
        {connected ? 'Đã kết nối' : 'Chưa kết nối'}
      </Text>
      <Button title={connected ? 'Ngắt kết nối' : 'Kết nối mũ'} onPress={onConnect} />
    </View>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16, backgroundColor: '#f0f0f0', borderRadius: 12, marginVertical: 10 },
  label: { fontSize: 16, fontWeight: '600' },
  status: { fontSize: 18, marginVertical: 8 },
  connected: { color: 'green' },
  disconnected: { color: 'red' },
});