const express = require('express');
const router = express.Router();

const { ingestTelemetry } = require('../controllers/telemetry.controller');
const validateTelemetry = require('../middlewares/validateTelemetry');

router.post('/telemetry', validateTelemetry, ingestTelemetry);

module.exports = router;
