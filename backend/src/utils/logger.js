// logger đơn giản (có thể thay bằng pino/winston sau)
module.exports = {
  info: (...a) => console.log('ℹ️', ...a),
  warn: (...a) => console.warn('⚠️', ...a),
  error: (...a) => console.error('❌', ...a)
};
