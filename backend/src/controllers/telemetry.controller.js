const { setCurrentPosition } = require('../services/position.service');
const { createIncident } = require('../services/incident.service');
const sockets = require('../sockets');
const { sendTelegramAlert } = require('../utils/telegram');
const Telemetry = require('../models/telemetry.model'); // optional

async function ingestTelemetry(req, res, next) {
  try {
    const { helmet_id, lat, lon, speed = 0, impact, ts } = req.body || {};

    // (tuỳ chọn) lưu log
    try { await Telemetry.create({ helmet_id, lat, lon, speed, impact_detected: impact, ts }); } catch {}

    // upsert vị trí hiện tại
    const pos = await setCurrentPosition(helmet_id, {
      lat, lon, speed, ts: new Date(ts)
    });
    sockets.emitPosition({ helmet_id, ...pos });

    if (impact) {
      await sendTelegramAlert(lat, lon);
      const incident = await createIncident({ helmet_id, lat, lon, ts: new Date(ts) });
      sockets.emitIncident(incident);
    }

    res.json({ ok: true });
  } catch (e) { next(e); }
}

module.exports = { ingestTelemetry };
