const {
  filePathFor,
  getProject,
  isAuthorized,
  readJson,
  unauthorized,
  writeJson,
} = require("./_store");

module.exports = async function handler(req, res) {
  if (!isAuthorized(req)) {
    return unauthorized(res);
  }

  const project = getProject(req);
  const snapshotPath = filePathFor(project, "snapshot");

  if (req.method === "GET") {
    const current = readJson(snapshotPath, { rows: [], updated_at: null });
    return res.status(200).json({
      ok: true,
      row_count: Array.isArray(current.rows) ? current.rows.length : 0,
      snapshot: Array.isArray(current.rows) ? current.rows : [],
      timestamp: current.updated_at || new Date().toISOString(),
    });
  }

  if (req.method === "POST") {
    const rows = req.body && Array.isArray(req.body.rows) ? req.body.rows : null;
    if (!rows) {
      return res.status(400).json({ ok: false, error: "rows must be an array" });
    }

    const payload = {
      rows,
      updated_at: new Date().toISOString(),
    };
    writeJson(snapshotPath, payload);

    return res.status(200).json({
      ok: true,
      row_count: rows.length,
      timestamp: payload.updated_at,
    });
  }

  return res.status(405).json({ ok: false, error: "Method not allowed" });
};
