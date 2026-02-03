// Quản lý Socket.IO (realtime)
let io = null;

function init(server, corsOrigin = '*') {
  const { Server } = require('socket.io');
  io = new Server(server, { cors: { origin: corsOrigin } });
  io.on('connection', (socket) => {
    // có thể join theo helmet_id nếu bạn muốn: socket.join(`helmet:${id}`)
    // console.log('socket connected', socket.id);
  });
}

function emitPosition(payload) {
  if (io) io.emit('position', payload);
}

function emitIncident(payload) {
  if (io) io.emit('incident', payload);
}

function emitIncidentAck(payload) {
  if (io) io.emit('incident_ack', payload);
}

module.exports = { init, emitPosition, emitIncident, emitIncidentAck };
