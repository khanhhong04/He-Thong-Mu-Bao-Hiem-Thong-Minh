const { getCurrentPosition } = require('../services/position.service');
const { ackIncident, listIncidents } = require('../services/incident.service');

// GET /api/position/:helmet_id
exports.getPosition = async (req, res, next) => {
  try {
    const pos = await getCurrentPosition(req.params.helmet_id);
    res.json(pos || null);
  } catch (e) { next(e); }
};

// GET /api/incidents
exports.getIncidents = async (_req, res, next) => {
  try {
    const list = await listIncidents();
    res.json(list);
  } catch (e) { next(e); }
};

// POST /api/incidents/:id/ack
exports.ack = async (req, res, next) => {
  try {
    const item = await ackIncident(req.params.id);
    if (!item) return res.status(404).json({ error: 'not_found' });
    try { require('../sockets').emitIncidentAck({ id: item._id?.toString?.() }); } catch {}
    res.json({ ok: true });
  } catch (e) { next(e); }
};
