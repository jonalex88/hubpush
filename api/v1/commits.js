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
  const commitsPath = filePathFor(project, "commits");

  if (req.method === "GET") {
    const allCommits = readJson(commitsPath, []);
    const parsedLimit = parseInt(String(req.query.limit || "0"), 10);
    const commits = Number.isFinite(parsedLimit) && parsedLimit > 0
      ? allCommits.slice(-parsedLimit)
      : allCommits;

    return res.status(200).json({
      ok: true,
      commits,
      timestamp: new Date().toISOString(),
    });
  }

  if (req.method === "POST") {
    const allCommits = readJson(commitsPath, []);
    const id = `commit-${new Date().toISOString().slice(0, 10)}-${String(allCommits.length + 1).padStart(3, "0")}`;

    const commit = {
      id,
      timestamp: new Date().toISOString(),
      undo_status: "none",
      ...(req.body || {}),
    };

    allCommits.push(commit);
    writeJson(commitsPath, allCommits);

    return res.status(200).json({
      ok: true,
      commit_id: commit.id,
      timestamp: commit.timestamp,
    });
  }

  return res.status(405).json({ ok: false, error: "Method not allowed" });
};
