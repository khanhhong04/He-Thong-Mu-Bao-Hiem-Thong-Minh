const mongoose = require('mongoose');
const logger = require('../utils/logger');

async function connectMongo(uri) {
  mongoose.set('strictQuery', true);
  mongoose.connection.on('connected', () => logger.info(' Mongo connected'));
  mongoose.connection.on('error', err => logger.error(' Mongo error:', err.message));
  mongoose.connection.on('disconnected', () => logger.warn(' Mongo disconnected'));
  await mongoose.connect(uri, { dbName: 'smarthelmet', serverSelectionTimeoutMS: 15000 });
}
module.exports = { connectMongo };
