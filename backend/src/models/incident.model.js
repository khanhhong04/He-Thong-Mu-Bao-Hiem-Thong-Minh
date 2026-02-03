const mongoose = require('mongoose');
const IncidentSchema = new mongoose.Schema({
  helmet_id: { type: String, index: true, required: true },
  lat: Number, lon: Number,
  ts: { type: Date, default: Date.now, index: true },
  ack: { type: Boolean, default: false }
}, { timestamps: true });
module.exports = mongoose.model('Incident', IncidentSchema, 'incidents');
