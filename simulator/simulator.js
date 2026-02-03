// simulator/simulator.js (Node.js, CommonJS)
const { nanoid } = require('nanoid');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// ==== CLI ===========================================================
const argv = yargs(hideBin(process.argv))
  .option('server',  { alias: 's', type: 'string', default: 'http://localhost:3000', describe: 'Backend base URL' })
  .option('helmet',  { alias: 'h', type: 'string', default: 'H001', describe: 'Helmet ID' })
  .option('scenario',{ alias: 'c', type: 'string', default: 'random', describe: 'Scenario name' })
  .option('interval',{ alias: 'i', type: 'number', default: 3000, describe: 'Send interval (ms)' })
  .option('lat',     { type: 'number', default: 21.02845, describe: 'Start lat' })
  .option('lon',     { type: 'number', default: 105.83591, describe: 'Start lon' })
  .option('verbose', { alias: 'v', type: 'boolean', default: true, describe: 'Print logs' })
  .help()
  .argv;

const BASE = argv.server.replace(/\/$/, '');
const TELEMETRY_URL = BASE + '/api/telemetry';

log(`▶ Simulator start: ${argv.scenario} | helmet=${argv.helmet} | ${TELEMETRY_URL} | every ${argv.interval}ms`);

// ==== Utilities =====================================================
function log(...args){ if (argv.verbose) console.log(...args); }
function frand(a,b){ return a + Math.random()*(b-a); }
function nowISO(){ return new Date().toISOString(); }

// Tạo "bước đi" nhỏ để lat/lon đổi nhẹ cho giống di chuyển
function drift(coord){ return coord + frand(-0.00005, 0.00005); }

// ==== Packet structure (mô phỏng cảm biến) ==========================
/*
  Chúng ta chỉ gửi lên backend các field:
  - helmet_id (mã mũ)
  - lat, lon (tọa độ)
  - speed (m/s) — giả lập
  - impact_detected (bool) — mô phỏng va chạm
  - ts (ISO-8601) — timestamp gửi
*/

// ===== 5 kịch bản + random =========================================
let step = 0;
let phase = 0;
let lat = argv.lat, lon = argv.lon;

function pkt_red_light(){       // Đứng đèn đỏ: still, no impact
  return { speed: 0, impact: false };
}
function pkt_traffic_jam(){     // Tắc đường: chậm, dao động nhỏ, no impact
  return { speed: frand(0,1.2), impact: false };
}
let emittedSpike = false;
function pkt_hard_brake(){      // Phanh gấp: 1 spike impact rồi vẫn đi (no still)
  if (!emittedSpike && step % 8 === 0) {
    emittedSpike = true;
    return { speed: 0.5, impact: true };
  }
  if (emittedSpike && step % 20 === 0) emittedSpike = false;
  return { speed: frand(3,8), impact: false };
}
function pkt_crash_then_still(){ // Va mạnh + nằm im nhiều tick
  // phase: 0 chạy, 1 impact, 2 still
  if (phase === 0) { phase = 1; return { speed: frand(8,12), impact: false }; }
  if (phase === 1) { phase = 2; return { speed: 0, impact: true }; }
  return { speed: 0, impact: false }; // still kéo dài
}
function pkt_rear_end_keep(){   // Bị húc nhưng không ngã: impact rồi vẫn di chuyển
  if (step % 5 === 0) return { speed: frand(2,6), impact: true };
  return { speed: frand(2,6), impact: false };
}
function pkt_rear_end_fall(){   // Bị húc + ngã: impact rồi speed=0 lâu
  if (phase === 0) { phase = 1; return { speed: frand(0,0.5), impact: false }; }  // sắp dừng đèn đỏ
  if (phase === 1) { phase = 2; return { speed: 0, impact: true }; }              // impact
  return { speed: 0, impact: false };                                             // nằm im
}
function pkt_random(){          // chế độ ngẫu nhiên
  return { speed: frand(0,12), impact: Math.random() < 0.03 };
}

// Map tên kịch bản → hàm sinh gói
const scenarios = {
  red: pkt_red_light,
  traffic: pkt_traffic_jam,
  brake: pkt_hard_brake,
  crash_still: pkt_crash_then_still,
  rear_end_keep: pkt_rear_end_keep,
  rear_end_fall: pkt_rear_end_fall,
  random: pkt_random
};

const scenarioFn = scenarios[argv.scenario] || pkt_random;

// ==== Sender loop ===================================================
const timer = setInterval(async () => {
  step++;

  // drift vị trí nhẹ nhàng
  lat = drift(lat);
  lon = drift(lon);

  // tạo gói theo kịch bản
  const { speed, impact } = scenarioFn();

  // JSON gửi backend (khớp firmware thật)
  const body = {
    helmet_id: argv.helmet,
    lat, lon,
    speed,
    impact_detected: impact,
    ts: nowISO()
  };

  try {
    const res = await fetch(TELEMETRY_URL, {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(body)
    });
    const ok = res.ok;
    const txt = await res.text().catch(()=> '');
    log(`POST ${ok?res.status:'ERR'} | impact=${impact} speed=${speed.toFixed(2)} | ${txt}`);
  } catch (e) {
    console.error('POST failed:', e.message);
  }
}, argv.interval);

// Ctrl+C to stop
process.on('SIGINT', () => {
  clearInterval(timer);
  console.log('\n⏹ Simulator stopped');
  process.exit(0);
});
