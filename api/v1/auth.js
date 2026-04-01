const crypto = require("crypto");
const { getProject, isAuthorized, unauthorized } = require("./_store");

// Credentials are stored in environment variables only — never in /tmp.
// HUBPUSH_USERS_JSON: JSON array of {username, pin_hash}
// HUBPUSH_AUTH_PEPPER: HMAC key used when generating pin_hash values
//
// Hash formula (must match generate_user_store.py):
//   HMAC-SHA256(key=pepper, message=username.toLowerCase() + ":" + pin)

function loadUsers() {
  const raw = process.env.HUBPUSH_USERS_JSON || "[]";
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_e) {
    return [];
  }
}

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

  const pepper = process.env.HUBPUSH_AUTH_PEPPER || "";
  if (!pepper) {
    console.error("HUBPUSH_AUTH_PEPPER is not set");
    return res.status(500).json({ ok: false, error: "Server configuration error" });
  }

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
