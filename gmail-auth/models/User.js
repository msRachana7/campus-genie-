const mongoose = require('mongoose');

const userSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    password: {
      type: String,
      required: true,
    },
    isVerified: {
      type: Boolean,
      default: false,
    },
    // Verification (signup) tokens — we store a HASH, never the raw token
    verificationTokenHash: String,
    verificationTokenExpiry: Date,

    // Forgot-password tokens — same pattern
    resetPasswordTokenHash: String,
    resetPasswordExpiry: Date,
  },
  { timestamps: true }
);

module.exports = mongoose.model('User', userSchema);
