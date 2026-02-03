const Incident = require('../models/incident.model');

async function createIncident({ helmet_id, lat, lon, ts }) {
  const doc = await Incident.create({ helmet_id, lat, lon, ts, ack: false });
  return doc.toObject();
}

async function ackIncident(id) {
  const doc = await Incident.findByIdAndUpdate(
    id,
    { $set: { ack: true } },
    { new: true }
  ).lean();
  return doc; // null nếu không tìm thấy
}

async function listIncidents() {
  const list = await Incident.find().sort({ ts: -1 }).lean();
  return list;
}

module.exports = { createIncident, ackIncident, listIncidents };
