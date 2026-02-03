const express = require('express');
const router = express.Router();

const ctrl = require('../controllers/incidents.controller');

router.get('/position/:helmet_id', ctrl.getPosition);
router.get('/incidents', ctrl.getIncidents);
router.post('/incidents/:id/ack', ctrl.ack);

module.exports = router;
