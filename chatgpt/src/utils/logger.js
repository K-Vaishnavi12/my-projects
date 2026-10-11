import fs from 'fs';
import path from 'path';

const LOG_DIR = path.resolve('logs');

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

const colors = {
  reset: '\x1b[0m',
  info: '\x1b[36m',     // Cyan
  warn: '\x1b[33m',     // Yellow
  error: '\x1b[31m',    // Red
  debug: '\x1b[90m',    // Gray
  success: '\x1b[32m'   // Green
};

function formatMessage(level, message, meta) {
  const timestamp = new Date().toISOString();
  const metaStr = meta && Object.keys(meta).length ? ` | ${JSON.stringify(meta)}` : '';
  return {
    timestamp,
    level,
    message,
    meta: meta || {}
  };
}

function writeToFile(logEntry) {
  const line = JSON.stringify(logEntry) + '\n';
  fs.appendFileSync(path.join(LOG_DIR, 'combined.log'), line);
  if (logEntry.level === 'error') {
    fs.appendFileSync(path.join(LOG_DIR, 'error.log'), line);
  }
}

export const logger = {
  info(msg, meta) {
    const entry = formatMessage('info', msg, meta);
    console.log(`${colors.info}[INFO]${colors.reset} [${entry.timestamp}] ${msg}`, meta ? colors.debug + JSON.stringify(meta) + colors.reset : '');
    writeToFile(entry);
  },
  success(msg, meta) {
    const entry = formatMessage('success', msg, meta);
    console.log(`${colors.success}[SUCCESS]${colors.reset} [${entry.timestamp}] ${msg}`, meta ? colors.debug + JSON.stringify(meta) + colors.reset : '');
    writeToFile(entry);
  },
  warn(msg, meta) {
    const entry = formatMessage('warn', msg, meta);
    console.warn(`${colors.warn}[WARN]${colors.reset} [${entry.timestamp}] ${msg}`, meta ? colors.debug + JSON.stringify(meta) + colors.reset : '');
    writeToFile(entry);
  },
  error(msg, error, meta) {
    const errMeta = error ? { error: error.message, stack: error.stack, ...meta } : meta;
    const entry = formatMessage('error', msg, errMeta);
    console.error(`${colors.error}[ERROR]${colors.reset} [${entry.timestamp}] ${msg}`, errMeta ? colors.debug + JSON.stringify(errMeta) + colors.reset : '');
    writeToFile(entry);
  },
  debug(msg, meta) {
    const entry = formatMessage('debug', msg, meta);
    // Only print debug logs if config or env allows, but write to file anyway
    if (process.env.DEBUG === 'true' || process.env.NODE_ENV === 'development') {
      console.log(`${colors.debug}[DEBUG] [${entry.timestamp}] ${msg}${colors.reset}`, meta ? JSON.stringify(meta) : '');
    }
    writeToFile(entry);
  }
};
