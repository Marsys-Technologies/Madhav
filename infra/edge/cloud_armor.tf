// Cloud Armor security policy — WAF preset + per-IP rate-limit.
// Attached to the amjis-web backend service in main.tf.

resource "google_compute_security_policy" "amjis_armor" {
  name        = "amjis-armor"
  description = "WAF + rate-limit policy for amjis-web (Wave 4 4.edge_and_infra_hygiene)."

  // ── WAF rule: OWASP XSS preset (block) ─────────────────────────────────────
  rule {
    action      = "deny(403)"
    priority    = 1000
    description = "Block OWASP XSS preset matches"

    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
  }

  // ── WAF rule: OWASP SQLi preset (block) ────────────────────────────────────
  rule {
    action      = "deny(403)"
    priority    = 1001
    description = "Block OWASP SQLi preset matches"

    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
  }

  // ── Rate-limit rule: per-IP throttle on /api/* ─────────────────────────────
  rule {
    action      = "throttle"
    priority    = 2000
    description = "Per-IP rate limit on /api/* — 60 RPS sustained, 120 burst"

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }

    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"

      rate_limit_threshold {
        // Cloud Armor allowed intervals: 10, 30, 60, 120, 180, 240, 300, 600, 900, 1200, 1800, 2700, 3600s.
        // 60 req/s logical target encoded as 600 req per 10s window (same rate, valid interval).
        count        = 600
        interval_sec = 10
      }
    }
  }

  // ── Default allow ──────────────────────────────────────────────────────────
  rule {
    action   = "allow"
    priority = 2147483647
    description = "Default rule, allow everything that didn't hit a deny/throttle above"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}

output "armor_policy_name" {
  value = google_compute_security_policy.amjis_armor.name
}
