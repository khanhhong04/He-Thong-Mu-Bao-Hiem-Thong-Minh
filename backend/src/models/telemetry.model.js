const mongoose = require('mongoose');
const TelemetrySchema = new mongoose.Schema({
  helmet_id: { type: String, index: true, required: true },
  lat: Number, lon: Number, speed: Number,
  impact_detected: Boolean,
  ts: { type: Date, default: Date.now, index: true }
}, { timestamps: true });
module.exports = mongoose.model('Telemetry', TelemetrySchema, 'telemetries');
