const crypto = require("crypto");
const { isAuthorized, unauthorized } = require("./_store");
const { loadPepper, loadUsers } = require("./_users");

// Credentials are stored in Vercel env vars when available, with a server-side
// hashed fallback to keep production auth functional if env injection is delayed.
// Hash formula (must match generate_user_store.py):
//   HMAC-SHA256(key=pepper, message=username.toLowerCase() + ":" + pin)

function computeHash(username, pin, pepper) {
  const message = `${username.toLowerCase()}:${pin}`;
  return crypto.createHmac("sha256", pepper).update(message).digest("hex");
}

function timingSafeEqual(a, b) {
  // Prevent timing-based oracle attacks on PIN comparison
  const bufA = Buffer.from(a, "hex");
  const bufB = Buffer.from(b, "hex");
  if (bufA.length !== bufB.length) {
    return false;
  }
  return crypto.timingSafeEqual(bufA, bufB);
}

module.exports = async function handler(req, res) {
  if (!isAuthorized(req)) {
    return unauthorized(res);
  }

  if (req.method !== "POST") {
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  const body = req.body || {};
  const username = typeof body.username === "string" ? body.username.trim() : "";
  const pin = typeof body.pin === "string" ? body.pin.trim() : "";

  if (!username || !pin) {
    return res.status(400).json({ ok: false, error: "username and pin are required" });
  }

  const pepper = loadPepper();

  const users = loadUsers();
  const user = users.find(
    (u) => typeof u.username === "string" && u.username.toLowerCase() === username.toLowerCase()
  );

  if (!user) {
    // Return same response as wrong PIN to avoid username enumeration
    return res.status(401).json({ ok: false, error: "Invalid username or PIN" });
  }

  const expectedHash = computeHash(username, pin, pepper);

  try {
    if (!timingSafeEqual(expectedHash, user.pin_hash)) {
      return res.status(401).json({ ok: false, error: "Invalid username or PIN" });
    }
  } catch (_e) {
    return res.status(401).json({ ok: false, error: "Invalid username or PIN" });
  }

  return res.status(200).json({
    ok: true,
    username: user.username,
    timestamp: new Date().toISOString(),
  });
};
