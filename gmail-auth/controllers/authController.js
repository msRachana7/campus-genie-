const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const User = require('../models/User');
const { generateToken, hashToken } = require('../utils/token');
const { isValidBmsceEmail } = require('../utils/validateEmail');
const sendEmail = require('../utils/sendEmail');

const CLIENT_URL = process.env.CLIENT_URL || 'http://localhost:3000';
const VERIFY_TOKEN_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const RESET_TOKEN_TTL_MS = 15 * 60 * 1000; // 15 minutes

// ---------------------------------------------------------------
// 1. SIGNUP — only @bmsce.ac.in allowed, account starts unverified
// ---------------------------------------------------------------
async function signup(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required.' });
    }

    if (!isValidBmsceEmail(email)) {
      return res.status(400).json({
        message: 'Only @bmsce.ac.in email addresses are allowed to register.',
      });
    }

    if (password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters.' });
    }

    const normalizedEmail = email.toLowerCase().trim();
    const existingUser = await User.findOne({ email: normalizedEmail });

    if (existingUser && existingUser.isVerified) {
      return res.status(409).json({ message: 'An account with this email already exists.' });
    }

    const hashedPassword = await bcrypt.hash(password, 12);
    const { rawToken, hashedToken } = generateToken();
    const verificationTokenExpiry = new Date(Date.now() + VERIFY_TOKEN_TTL_MS);

    let user;
    if (existingUser && !existingUser.isVerified) {
      // Re-registering before verifying: overwrite the old pending signup
      existingUser.password = hashedPassword;
      existingUser.verificationTokenHash = hashedToken;
      existingUser.verificationTokenExpiry = verificationTokenExpiry;
      user = await existingUser.save();
    } else {
      user = await User.create({
        email: normalizedEmail,
        password: hashedPassword,
        isVerified: false,
        verificationTokenHash: hashedToken,
        verificationTokenExpiry,
      });
    }

    const verifyLink = `${CLIENT_URL}/verify-email?token=${rawToken}&email=${encodeURIComponent(
      user.email
    )}`;

    await sendEmail({
      to: user.email,
      subject: 'Verify your BMSCE account',
      html: `
        <p>Welcome! Please verify your email address to activate your account.</p>
        <p><a href="${verifyLink}">Click here to verify your email</a></p>
        <p>This link expires in 24 hours. If you didn't request this, you can ignore this email.</p>
      `,
    });

    return res.status(201).json({
      message: 'Signup successful. Please check your email to verify your account before logging in.',
    });
  } catch (err) {
    console.error('Signup error:', err);
    return res.status(500).json({ message: 'Something went wrong during signup.' });
  }
}

// ---------------------------------------------------------------
// 2. VERIFY EMAIL — activates the account
// ---------------------------------------------------------------
async function verifyEmail(req, res) {
  try {
    const { token, email } = req.query;

    if (!token || !email) {
      return res.status(400).json({ message: 'Invalid verification link.' });
    }

    const user = await User.findOne({ email: email.toLowerCase().trim() });

    if (!user) {
      return res.status(400).json({ message: 'Invalid verification link.' });
    }

    if (user.isVerified) {
      return res.status(200).json({ message: 'Email already verified. You can log in.' });
    }

    const hashedIncomingToken = hashToken(token);
    const isTokenValid =
      user.verificationTokenHash === hashedIncomingToken &&
      user.verificationTokenExpiry &&
      user.verificationTokenExpiry.getTime() > Date.now();

    if (!isTokenValid) {
      return res.status(400).json({ message: 'Verification link is invalid or has expired.' });
    }

    user.isVerified = true;
    user.verificationTokenHash = undefined;
    user.verificationTokenExpiry = undefined;
    await user.save();

    return res.status(200).json({ message: 'Email verified successfully. You can now log in.' });
  } catch (err) {
    console.error('Verify email error:', err);
    return res.status(500).json({ message: 'Something went wrong during verification.' });
  }
}

// ---------------------------------------------------------------
// 3. LOGIN — blocked until email is verified
// ---------------------------------------------------------------
async function login(req, res) {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required.' });
    }

    const user = await User.findOne({ email: email.toLowerCase().trim() });

    // Same generic message whether the user doesn't exist or the password
    // is wrong — avoids leaking which emails are registered.
    if (!user) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    if (!user.isVerified) {
      return res.status(403).json({
        message: 'Please verify your email before logging in. Check your inbox for the verification link.',
      });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    const token = jwt.sign({ userId: user._id, email: user.email }, process.env.JWT_SECRET, {
      expiresIn: '7d',
    });

    return res.status(200).json({
      message: 'Login successful.',
      token,
      user: { id: user._id, email: user.email },
    });
  } catch (err) {
    console.error('Login error:', err);
    return res.status(500).json({ message: 'Something went wrong during login.' });
  }
}

// ---------------------------------------------------------------
// 4. FORGOT PASSWORD — sends a reset link (short-lived token)
// ---------------------------------------------------------------
async function forgotPassword(req, res) {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ message: 'Email is required.' });
    }

    const user = await User.findOne({ email: email.toLowerCase().trim() });

    // Always respond with a generic success message, even if the user
    // doesn't exist — prevents attackers from probing which emails are registered.
    const genericResponse = {
      message: 'If an account with that email exists, a password reset link has been sent.',
    };

    if (!user || !user.isVerified) {
      return res.status(200).json(genericResponse);
    }

    const { rawToken, hashedToken } = generateToken();
    user.resetPasswordTokenHash = hashedToken;
    user.resetPasswordExpiry = new Date(Date.now() + RESET_TOKEN_TTL_MS);
    await user.save();

    const resetLink = `${CLIENT_URL}/reset-password?token=${rawToken}&email=${encodeURIComponent(
      user.email
    )}`;

    await sendEmail({
      to: user.email,
      subject: 'Reset your BMSCE account password',
      html: `
        <p>We received a request to reset your password.</p>
        <p><a href="${resetLink}">Click here to reset your password</a></p>
        <p>This link expires in 15 minutes. If you didn't request this, you can safely ignore this email.</p>
      `,
    });

    return res.status(200).json(genericResponse);
  } catch (err) {
    console.error('Forgot password error:', err);
    return res.status(500).json({ message: 'Something went wrong. Please try again.' });
  }
}

// ---------------------------------------------------------------
// 5. RESET PASSWORD — consumes the token, sets new password
// ---------------------------------------------------------------
async function resetPassword(req, res) {
  try {
    const { token, email, newPassword } = req.body;

    if (!token || !email || !newPassword) {
      return res.status(400).json({ message: 'Token, email, and new password are required.' });
    }

    if (newPassword.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters.' });
    }

    const user = await User.findOne({ email: email.toLowerCase().trim() });
    if (!user) {
      return res.status(400).json({ message: 'Invalid or expired reset link.' });
    }

    const hashedIncomingToken = hashToken(token);
    const isTokenValid =
      user.resetPasswordTokenHash === hashedIncomingToken &&
      user.resetPasswordExpiry &&
      user.resetPasswordExpiry.getTime() > Date.now();

    if (!isTokenValid) {
      return res.status(400).json({ message: 'Invalid or expired reset link.' });
    }

    user.password = await bcrypt.hash(newPassword, 12);
    user.resetPasswordTokenHash = undefined;
    user.resetPasswordExpiry = undefined;
    await user.save();

    return res.status(200).json({ message: 'Password reset successful. You can now log in.' });
  } catch (err) {
    console.error('Reset password error:', err);
    return res.status(500).json({ message: 'Something went wrong resetting your password.' });
  }
}

module.exports = { signup, verifyEmail, login, forgotPassword, resetPassword };
