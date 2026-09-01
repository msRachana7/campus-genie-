// Only accepts addresses ending in @bmsce.ac.in (case-insensitive)
const BMSCE_EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@bmsce\.ac\.in$/i;

function isValidBmsceEmail(email) {
  if (!email || typeof email !== 'string') return false;
  return BMSCE_EMAIL_REGEX.test(email.trim());
}

module.exports = { isValidBmsceEmail };
