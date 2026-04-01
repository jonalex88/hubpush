const { getProject } = require("./_store");

module.exports = async function handler(req, res) {
  const project = getProject(req);
  return res.status(200).json({
    ok: true,
    backend: "vercel-tmp-file",
    project,
    timestamp: new Date().toISOString(),
    note: "Storage is ephemeral unless replaced with durable backend (for example, Vercel KV).",
  });
};
