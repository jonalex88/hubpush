const { isAuthorized, unauthorized } = require("./_store");
const { loadUsers } = require("./_users");

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
