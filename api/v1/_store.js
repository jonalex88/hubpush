const fs = require("fs");
const path = require("path");

const TMP_DIR = "/tmp/hubpush";

function ensureTmpDir() {
  if (!fs.existsSync(TMP_DIR)) {
    fs.mkdirSync(TMP_DIR, { recursive: true });
  }
}

function filePathFor(project, name) {
  ensureTmpDir();
  return path.join(TMP_DIR, `${project}.${name}.json`);
}

function readJson(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) {
      return fallback;
    }
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw);
  } catch (_err) {
    return fallback;
  }
}

function writeJson(filePath, value) {
  const body = JSON.stringify(value, null, 2);
  fs.writeFileSync(filePath, body, "utf-8");
}

function getProject(req) {
  return String(req.headers["x-project"] || process.env.HUBPUSH_PROJECT || "hubpush");
}

function isAuthorized(req) {
  const expected = process.env.HUBPUSH_CLOUD_API_KEY || "";
  if (!expected) {
    return true;
  }
  const provided = String(req.headers["x-api-key"] || "");
  return provided && provided === expected;
}

function unauthorized(res) {
  return res.status(401).json({ ok: false, error: "Unauthorized" });
}

module.exports = {
  filePathFor,
  getProject,
  isAuthorized,
  readJson,
  unauthorized,
  writeJson,
};
