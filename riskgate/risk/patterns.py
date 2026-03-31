from __future__ import annotations

SECURITY_PATTERNS = [
    {"name": "crypto", "pattern": r"(AES|RSA|SHA|hmac|encrypt|decrypt)", "weight": 1.0},
    {"name": "auth", "pattern": r"(jwt|token|session|password|authenticate)", "weight": 0.9},
    {"name": "sql", "pattern": r"(execute|cursor\.execute|raw\()", "weight": 0.8},
    {"name": "secrets", "pattern": r"(os\\.environ|getenv|SECRET|API_KEY)", "weight": 0.7},
    {"name": "file_io", "pattern": r"(open\(|write\(|os\.remove)", "weight": 0.5},
]

INFRA_PATTERNS = [
    "Dockerfile",
    "*.tf",
    "*.tfvars",
    ".github/*.yml",
    "migrations/",
    "package.json",
    "requirements.txt",
]
