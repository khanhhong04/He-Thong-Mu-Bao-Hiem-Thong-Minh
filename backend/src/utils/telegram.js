// backend/src/utils/telegram.js
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

// TOKEN CỦA BẠN
const TOKEN = '8217786021:AAHojN31Bx1xV_9DXK2klf5xxqIUacWFc6E';

// CHAT_ID CỦA BẠN – ĐÃ LẤY TỪ getUpdates
const CHAT_ID = '5843805498';  // ← ĐÃ DÁN VÀO ĐÂY

const sendTelegramAlert = async (lat, lon) => {
  const mapsUrl = `https://maps.google.com/?q=${lat},${lon}`;
  const message = `
*CẢNH BÁO: VA CHẠM MẠNH!*  
Vị trí: [Mở Google Maps](${mapsUrl})
Thời gian: ${new Date().toLocaleString('vi-VN')}
  `.trim();

  try {
    await fetch(`https://api.telegram.org/bot${TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: message,
        parse_mode: 'Markdown',
        disable_web_page_preview: false
      })
    });
    console.log('ĐÃ GỬI TELEGRAM:', mapsUrl);
  } catch (error) {
    console.error('Lỗi gửi Telegram:', error.message);
  }
};

module.exports = { sendTelegramAlert };