const { getProject, isAuthorized, unauthorized } = require("./_store");

// Users are read from HUBPUSH_USERS_JSON env var (array of {username, pin_hash})
// This endpoint returns only usernames — never hashes or PINs.
function loadUsers() {
  const raw = process.env.HUBPUSH_USERS_JSON || "[]";
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_e) {
    return [];
  }
}

module.exports = async function handler(req, res) {
  if (!isAuthorized(req)) {
    return unauthorized(res);
  }
  if (req.method !== "GET") {
    return res.status(405).json({ ok: false, error: "Method not allowed" });
  }

  const users = loadUsers();
  const usernames = users.map((u) => u.username).filter(Boolean);

  return res.status(200).json({
    ok: true,
    users: usernames,
    timestamp: new Date().toISOString(),
  });
};
