const PositionCurrent = require('../models/position.model');

async function setCurrentPosition(helmet_id, pos) {
  return await PositionCurrent.findOneAndUpdate(
    { helmet_id },
    { ...pos, helmet_id },
    { new: true, upsert: true, setDefaultsOnInsert: true }
  ).lean();
}

async function getCurrentPosition(helmet_id) {
  return await PositionCurrent.findOne({ helmet_id }).lean();
}

module.exports = { setCurrentPosition, getCurrentPosition };
