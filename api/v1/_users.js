const FALLBACK_USERS = [
  {
    username: "Yusuf S",
    pin_hash: "da223190052be740544035bf17dc6db84cfea05b5ae48a1993b0c5ce6f0d7990",
  },
  {
    username: "Michelle",
    pin_hash: "5f63cba8573d4efe414819df175bb150af0897ad83ca4f4cafb4f3d6fb8c8d8c",
  },
  {
    username: "Meehgan",
    pin_hash: "7811d38ca078025e94ca780de16985ea1bb3f237645ff02e0b7a2b452da5b2c6",
  },
  {
    username: "Jonathan",
    pin_hash: "61b3cf10a8d1b2fd40a54f1ec82a06f126f540f0b9ccefbefd8d90729bd93aeb",
  },
  {
    username: "AD",
    pin_hash: "465ed19a9aaadc73f02c334e15ebdcb449512b188410b9a723044c3c96a54098",
  },
  {
    username: "Cheslin",
    pin_hash: "30bdf3d6f16f0944e3759b0496346eaa875508aac809dbf456e24f5e723c8670",
  },
];

const FALLBACK_PEPPER = "YLR-ek3H6-vO9R5w0jb7lR5hDs_vFrgDKgZ8co4lLoU";

function parseUsersEnv(rawValue) {
  if (!rawValue) {
    return null;
  }

  const normalized = String(rawValue).trim();
  const candidates = [
    normalized,
    normalized.replace(/^JSON:\s*/i, ""),
    normalized.replace(/;\s*$/, ""),
    normalized.replace(/^JSON:\s*/i, "").replace(/;\s*$/, ""),
  ];

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    } catch (_err) {
      // Keep trying normalized variants.
    }
  }

  return null;
}

function loadUsers() {
  const parsed = parseUsersEnv(process.env.HUBPUSH_USERS_JSON || "");
  return parsed || FALLBACK_USERS;
}

function loadPepper() {
  const value = String(process.env.HUBPUSH_AUTH_PEPPER || "").trim();
  return value || FALLBACK_PEPPER;
}

module.exports = {
  loadPepper,
  loadUsers,
};