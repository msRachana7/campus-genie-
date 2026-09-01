const crypto = require('crypto');

/**
 * Generates a random raw token (sent to the user via email/link)
 * and its SHA-256 hash (stored in the DB).
 * We never store the raw token — if the DB leaks, tokens can't be reused.
 */
function generateToken() {
  const rawToken = crypto.randomBytes(32).toString('hex');
  const hashedToken = crypto.createHash('sha256').update(rawToken).digest('hex');
  return { rawToken, hashedToken };
}

function hashToken(rawToken) {
  return crypto.createHash('sha256').update(rawToken).digest('hex');
}

module.exports = { generateToken, hashToken };
