const express = require('express');
const router = express.Router();

router.get('/', (_req, res) => res.send('Smart Helmet API OK'));

module.exports = router;
