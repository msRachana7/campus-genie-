const express = require('express');
const router = express.Router();

const {
  signup,
  verifyEmail,
  login,
  forgotPassword,
  resetPassword,
} = require('../controllers/authController');

router.post('/signup', signup);
router.get('/verify-email', verifyEmail);       // ?token=...&email=...
router.post('/login', login);
router.post('/forgot-password', forgotPassword);
router.post('/reset-password', resetPassword);

module.exports = router;
