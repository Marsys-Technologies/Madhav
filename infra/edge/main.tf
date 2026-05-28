// MARSYS-JIS Platform Modernization — Wave 4 unit 4.edge_and_infra_hygiene
//
// External HTTPS load balancer + Cloud CDN in front of amjis-web Cloud Run.
// IaC only. DO NOT run apply from this worktree.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

variable "gcp_project" {
  type    = string
  default = "madhav-astrology"
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"
}

variable "domain_name" {
  type        = string
  description = "Public domain served by the LB (e.g. amjis.madhavstreamc.io). Managed cert is provisioned for this name."
  default     = "amjis.madhavstreamc.io"
}

variable "cloud_run_service_name" {
  type    = string
  default = "amjis-web"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

// ── Serverless NEG fronting Cloud Run ────────────────────────────────────────

resource "google_compute_region_network_endpoint_group" "amjis_web_neg" {
  name                  = "amjis-web-neg"
  region                = var.gcp_region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = var.cloud_run_service_name
  }
}

// ── Backend service with Cloud CDN enabled ───────────────────────────────────

resource "google_compute_backend_service" "amjis_web_cdn" {
  name                  = "amjis-web-backend"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  enable_cdn            = true

  backend {
    group = google_compute_region_network_endpoint_group.amjis_web_neg.id
  }

  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    client_ttl                   = 3600
    default_ttl                  = 3600
    max_ttl                      = 86400
    negative_caching             = true
    serve_while_stale            = 86400
    signed_url_cache_max_age_sec = 0

    cache_key_policy {
      include_host         = true
      include_protocol     = true
      include_query_string = true
    }
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }

  security_policy = google_compute_security_policy.amjis_armor.id
}

// ── URL map: path-based routing for static + chart-document caching ──────────

resource "google_compute_url_map" "amjis_web_urlmap" {
  name            = "amjis-web-urlmap"
  default_service = google_compute_backend_service.amjis_web_cdn.id

  host_rule {
    hosts        = [var.domain_name]
    path_matcher = "main"
  }

  path_matcher {
    name            = "main"
    default_service = google_compute_backend_service.amjis_web_cdn.id

    // _next/static/* → long-lived immutable.
    path_rule {
      paths   = ["/_next/static/*"]
      service = google_compute_backend_service.amjis_web_cdn.id
      route_action {
        url_rewrite {
          path_prefix_rewrite = "/_next/static/"
        }
      }
    }

    // Chart documents → 5-min CDN cache (revalidated by ETag).
    path_rule {
      paths   = ["/api/charts/*/document"]
      service = google_compute_backend_service.amjis_web_cdn.id
    }
  }
}

// ── HTTPS proxy + managed certificate + global forwarding rule ───────────────

resource "google_compute_managed_ssl_certificate" "amjis_cert" {
  name = "amjis-web-cert"

  managed {
    domains = [var.domain_name]
  }
}

resource "google_compute_target_https_proxy" "amjis_https_proxy" {
  name             = "amjis-web-https-proxy"
  url_map          = google_compute_url_map.amjis_web_urlmap.id
  ssl_certificates = [google_compute_managed_ssl_certificate.amjis_cert.id]
}

resource "google_compute_global_address" "amjis_lb_ip" {
  name = "amjis-web-lb-ip"
}

resource "google_compute_global_forwarding_rule" "amjis_https_fr" {
  name                  = "amjis-web-https-fr"
  ip_address            = google_compute_global_address.amjis_lb_ip.address
  port_range            = "443"
  target                = google_compute_target_https_proxy.amjis_https_proxy.id
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

output "lb_ip" {
  value       = google_compute_global_address.amjis_lb_ip.address
  description = "Public IP of the LB — point DNS A-record here."
}

output "cdn_backend_name" {
  value = google_compute_backend_service.amjis_web_cdn.name
}
