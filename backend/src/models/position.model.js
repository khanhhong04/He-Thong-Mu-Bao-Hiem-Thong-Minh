const mongoose = require('mongoose');

const PositionSchema = new mongoose.Schema({
  helmet_id: { type: String, unique: true, index: true, required: true },
  lat: { type: Number, required: true },
  lon: { type: Number, required: true },
  speed: { type: Number, default: 0 },
  ts: { type: Date, default: Date.now }
}, { timestamps: true });

module.exports = mongoose.model('PositionCurrent', PositionSchema, 'positions_current');
