const logger = require('../utils/logger');

// Error handler chuẩn Express (Express 5 hỗ trợ async handler)
function errorHandler(err, _req, res, _next) {
  logger.error(err.stack || err.message || err);
  res.status(500).json({ error: 'internal_error' });
}

module.exports = errorHandler;
