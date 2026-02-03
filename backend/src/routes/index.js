const express = require('express');
const router = express.Router();
router.use('/', require('./health.routes'));
router.use('/api', require('./telemetry.routes'));
router.use('/api', require('./incidents.routes'));
module.exports = router;
