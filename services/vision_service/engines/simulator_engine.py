"""
BlindWatch Simulator Engine
----------------------------
Runs privacy vs. safety comparative simulations.

Formulas (Volume 5 specification):

  safety_score  = camera_coverage * 0.3
                + threat_detection * 0.4
                + response_speed   * 0.3

  fpr           = sensitivity * crowd_density_factor

  bias_risk     = tracking_intensity * identity_collection_factor

  trust_score   = privacy_score * 0.5
                + compliance_score * 0.3
                + transparency_score * 0.2

Traditional CCTV baselines:
  privacy_score = 25   trust_score = 30   safety_score = 75
"""
import math
import datetime
from typing import Dict


# ── Lookup helpers ─────────────────────────────────────────────────────────────

_CROWD_FACTORS = {"low": 0.2, "medium": 0.5, "high": 1.0}
_THREAT_FACTORS = {"low": 0.3, "medium": 0.6, "high": 0.9}
_IDENTITY_FACTORS = {
    "anonymized_only":    0.0,
    "stored_by_default":  0.5,
    "raw_biometric":      1.0,
}

# Traditional CCTV baseline (constant)
TRADITIONAL_BASELINE = {
    "privacy_score":        25.0,
    "safety_score":         75.0,
    "trust_score":          30.0,
    "compliance_score":     35.0,
    "false_positive_rate":  0.30,
    "bias_risk":            0.70,
    "transparency_score":   20.0,
}


class SimulatorEngine:
    """
    Runs a BlindWatch policy simulation and returns comparative metrics
    against the Traditional CCTV baseline.
    """

    @classmethod
    def run(
        cls,
        cameras_count: int         = 12,
        retention_days: int        = 7,
        sensitivity: float         = 0.75,     # 0.0–1.0
        identity_collection: str   = "anonymized_only",
        crowd_density: str         = "medium",  # low | medium | high
        threat_level: str          = "medium",  # low | medium | high
        config_name: str           = "Simulation Run",
    ) -> Dict:

        cameras_count  = max(1, cameras_count)
        sensitivity    = max(0.0, min(1.0, sensitivity))
        crowd_factor   = _CROWD_FACTORS.get(crowd_density, 0.5)
        threat_factor  = _THREAT_FACTORS.get(threat_level, 0.6)
        identity_factor = _IDENTITY_FACTORS.get(identity_collection, 0.0)

        # ── BlindWatch Privacy Score ──────────────────────────────────────
        from services.vision_service.engines.privacy_engine import PrivacyScoreEngine, ComplianceEngine, TrustEngine

        privacy_result     = PrivacyScoreEngine.calculate(
            identity_collection    = identity_collection,
            retention_days         = retention_days,
            avg_tracking_minutes   = 15.0,
            data_sharing_enabled   = False,
            access_controls_strict = True,
        )
        compliance_result  = ComplianceEngine.check(
            identity_collection    = identity_collection,
            retention_days         = retention_days,
        )
        transparency_score = 95.0  # BlindWatch default

        bw_privacy_score     = privacy_result["privacy_score"]
        bw_compliance_score  = compliance_result["compliance_score"]
        bw_trust_score       = TrustEngine.calculate(bw_privacy_score, bw_compliance_score, transparency_score)

        # ── BlindWatch Safety Score ───────────────────────────────────────
        # camera_coverage: more cameras = better coverage, capped at 1.0
        camera_coverage  = min(1.0, cameras_count / 20.0)
        # threat_detection: driven by sensitivity and threat level
        threat_detection = sensitivity * threat_factor
        # response_speed:  inversely related to retention (privacy-first may add ms latency)
        retention_penalty = min(0.2, retention_days / 90.0 * 0.2)
        response_speed   = max(0.5, 1.0 - retention_penalty)

        bw_safety_score = round(
            (camera_coverage  * 0.30
             + threat_detection * 0.40
             + response_speed   * 0.30) * 100,
            1
        )

        # ── False Positive Rate ───────────────────────────────────────────
        bw_fpr = round(sensitivity * crowd_factor * 0.25, 3)   # BlindWatch has extra filtering

        # ── Bias Risk ─────────────────────────────────────────────────────
        # tracking_intensity: proxy for detection sensitivity
        tracking_intensity = sensitivity
        bw_bias = round(tracking_intensity * identity_factor * 0.15, 3)   # anonymization reduces bias

        # ── Traditional CCTV adjusted to current config ───────────────────
        trad_safety = round(min(99.0, 50.0 + cameras_count * 1.5 + sensitivity * 10), 1)
        trad_fpr    = round(sensitivity * crowd_factor * 0.60, 3)         # no AI filtering
        trad_bias   = round(tracking_intensity * max(identity_factor, 0.5) * 0.80, 3)

        # ── Recommendations ───────────────────────────────────────────────
        recs = cls._generate_recommendations(
            privacy_score=bw_privacy_score,
            safety_score=bw_safety_score,
            compliance_findings=compliance_result.get("findings", []),
            retention_days=retention_days,
            identity_collection=identity_collection,
        )

        return {
            "config_name":     config_name,
            "timestamp":       datetime.datetime.utcnow().isoformat(),
            "blindwatch": {
                "privacy_score":       bw_privacy_score,
                "safety_score":        bw_safety_score,
                "trust_score":         bw_trust_score,
                "compliance_score":    bw_compliance_score,
                "transparency_score":  transparency_score,
                "false_positive_rate": bw_fpr,
                "bias_risk":           bw_bias,
            },
            "traditional": {
                "privacy_score":       TRADITIONAL_BASELINE["privacy_score"],
                "safety_score":        trad_safety,
                "trust_score":         TRADITIONAL_BASELINE["trust_score"],
                "compliance_score":    TRADITIONAL_BASELINE["compliance_score"],
                "transparency_score":  TRADITIONAL_BASELINE["transparency_score"],
                "false_positive_rate": trad_fpr,
                "bias_risk":           trad_bias,
            },
            "inputs": {
                "cameras_count":       cameras_count,
                "retention_days":      retention_days,
                "sensitivity":         sensitivity,
                "identity_collection": identity_collection,
                "crowd_density":       crowd_density,
                "threat_level":        threat_level,
            },
            "recommendations": recs,
            "compliance_findings": compliance_result.get("findings", []),
        }

    @staticmethod
    def _generate_recommendations(
        privacy_score: float,
        safety_score: float,
        compliance_findings: list,
        retention_days: int,
        identity_collection: str,
    ) -> list:
        recs = []
        if privacy_score < 80:
            recs.append("Switch to anonymized-only identity mode to improve privacy score.")
        if retention_days > 14:
            recs.append(f"Reduce data retention from {retention_days} days to ≤7 days (GDPR optimization).")
        if identity_collection != "anonymized_only":
            recs.append("Enable SHA-256 anonymous entity hashing – destroy raw identity at source.")
        if safety_score < 70:
            recs.append("Add camera nodes to underserved zones to improve coverage score.")
        if compliance_findings:
            recs.append("Address compliance findings: " + "; ".join(compliance_findings[:2]))
        recs.append("Enable double-blind authorization locks on high-risk zone camera nodes.")
        return recs
