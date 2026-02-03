const express = require('express');
const cors = require('cors');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');
const { CORS_ORIGIN } = require('./config');

const app = express();

// Middleware cơ bản
app.use(cors({ origin: CORS_ORIGIN })); // CORS (Cross-Origin Resource Sharing)
app.use(express.json());                // parse JSON

// Routes
app.use(routes);

// Error handler (đặt sau routes)
app.use(errorHandler);

module.exports = app;
