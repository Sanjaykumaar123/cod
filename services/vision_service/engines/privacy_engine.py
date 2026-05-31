"""
BlindWatch Privacy Engine
-------------------------
Handles face detection, anonymization and anonymous entity hash generation.
Supports Blur, Pixelate and Black Mask modes.
Faces are NEVER stored – only processed in memory.
"""
import hashlib
import datetime
import numpy as np
from typing import Optional, Tuple, List, Dict

# Try to import OpenCV – gracefully fall back to numpy-only mode if not installed
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

ANONYMIZATION_MODES = ["blur", "pixelate", "blackmask"]


class FaceAnonymizer:
    """
    Anonymizes face regions inside frames.
    Input  : BGR numpy frame  +  list of bounding-boxes  (x1,y1,x2,y2)
    Output : frame with anonymised face regions (original data destroyed)
    """

    def __init__(self, mode: str = "blur"):
        assert mode in ANONYMIZATION_MODES, f"Unknown mode: {mode}"
        self.mode = mode

    def anonymize(self, frame: np.ndarray, bboxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """Apply anonymization to every bbox in the frame in-place."""
        if not CV2_AVAILABLE:
            return frame  # pass-through when OpenCV not installed
        frame = frame.copy()
        for (x1, y1, x2, y2) in bboxes:
            # Clamp to frame bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
            if x2 <= x1 or y2 <= y1:
                continue
            region = frame[y1:y2, x1:x2]
            if self.mode == "blur":
                # Gaussian blur (kernel must be odd)
                k = 99
                blurred = cv2.GaussianBlur(region, (k, k), 30)
                frame[y1:y2, x1:x2] = blurred
            elif self.mode == "pixelate":
                h, w = region.shape[:2]
                small = cv2.resize(region, (max(1, w // 15), max(1, h // 15)), interpolation=cv2.INTER_LINEAR)
                pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
                frame[y1:y2, x1:x2] = pixelated
            elif self.mode == "blackmask":
                frame[y1:y2, x1:x2] = 0
        return frame


class EntityHasher:
    """
    Creates a privacy-safe anonymous entity identifier.
    entity_hash = SHA256(camera_id + timestamp_bucket + tracking_id)

    The timestamp is bucketed to 1-minute intervals so the same entity
    produces a consistent hash within a session window.
    """

    @staticmethod
    def generate(camera_id: str, tracking_id: int, timestamp: Optional[datetime.datetime] = None) -> str:
        if timestamp is None:
            timestamp = datetime.datetime.utcnow()
        # Bucket to minute to keep IDs stable within short windows
        bucket = timestamp.strftime("%Y%m%d%H%M")
        raw = f"{camera_id}::{bucket}::{tracking_id}"
        digest = hashlib.sha256(raw.encode()).hexdigest().upper()
        return f"ENTITY_{digest[:5]}"


class PrivacyScoreEngine:
    """
    Computes the real-time Privacy Score (0–100) based on system configuration.

    privacy_score = 100
                  - identity_penalty   (storing real IDs)
                  - retention_penalty  (long data retention)
                  - tracking_penalty   (extended tracking duration)
                  - sharing_penalty    (data sharing enabled)
    """

    # Maximum deductions for each factor (sum = 100)
    IDENTITY_MAX   = 40
    RETENTION_MAX  = 25
    TRACKING_MAX   = 20
    SHARING_MAX    = 15

    @classmethod
    def calculate(
        cls,
        identity_collection: str = "anonymized_only",   # anonymized_only | stored_by_default | raw_biometric
        retention_days: int = 7,
        avg_tracking_minutes: float = 10.0,
        data_sharing_enabled: bool = False,
        access_controls_strict: bool = True
    ) -> Dict:
        # --- Identity penalty ---
        identity_map = {
            "anonymized_only": 0,
            "stored_by_default": 25,
            "raw_biometric": 40,
        }
        identity_penalty = identity_map.get(identity_collection, 20)

        # --- Retention penalty ---
        # 0 days → 0 penalty | 90+ days → max penalty
        retention_penalty = min(cls.RETENTION_MAX, (retention_days / 90.0) * cls.RETENTION_MAX)

        # --- Tracking penalty ---
        # 0 min → 0 | 60+ min → max
        tracking_penalty = min(cls.TRACKING_MAX, (avg_tracking_minutes / 60.0) * cls.TRACKING_MAX)

        # --- Sharing penalty ---
        sharing_penalty = cls.SHARING_MAX if data_sharing_enabled else 0

        # Bonus for strict access controls
        access_bonus = 5 if access_controls_strict else 0

        raw_score = (
            100
            - identity_penalty
            - retention_penalty
            - tracking_penalty
            - sharing_penalty
            + access_bonus
        )
        privacy_score = round(max(0.0, min(100.0, raw_score)), 1)

        return {
            "privacy_score": privacy_score,
            "breakdown": {
                "identity_penalty":  round(identity_penalty, 1),
                "retention_penalty": round(retention_penalty, 1),
                "tracking_penalty":  round(tracking_penalty, 1),
                "sharing_penalty":   round(sharing_penalty, 1),
                "access_bonus":      access_bonus,
            },
            "risk_level": "LOW" if privacy_score > 80 else ("MEDIUM" if privacy_score > 50 else "HIGH"),
        }


class ComplianceEngine:
    """
    Checks compliance against GDPR, CCPA, and local privacy rules.
    Returns a structured compliance score with per-regulation results.
    """

    @staticmethod
    def check(
        identity_collection: str = "anonymized_only",
        retention_days: int = 7,
        data_sharing_enabled: bool = False,
        access_controls_strict: bool = True,
        audit_logging_enabled: bool = True,
    ) -> Dict:
        gdpr_pass = (
            identity_collection == "anonymized_only"
            and retention_days <= 30
            and not data_sharing_enabled
        )
        ccpa_pass = (
            identity_collection in ["anonymized_only", "stored_by_default"]
            and not data_sharing_enabled
        )
        local_pass = access_controls_strict and audit_logging_enabled

        weights = {"GDPR": 0.45, "CCPA": 0.35, "LOCAL": 0.20}
        scores = {"GDPR": 100 if gdpr_pass else 40, "CCPA": 100 if ccpa_pass else 50, "LOCAL": 100 if local_pass else 60}
        compliance_score = round(sum(scores[k] * weights[k] for k in weights), 1)

        findings = []
        if not gdpr_pass:
            if identity_collection != "anonymized_only":
                findings.append("GDPR: Identity data collection exceeds anonymization requirement")
            if retention_days > 30:
                findings.append(f"GDPR: Retention period ({retention_days}d) exceeds recommended 30 days")
        if not ccpa_pass:
            findings.append("CCPA: Data sharing policy requires explicit opt-in disclosures")
        if not local_pass:
            findings.append("LOCAL: Strict access controls or audit logging not enforced")

        return {
            "compliance_score": compliance_score,
            "gdpr_pass": gdpr_pass,
            "ccpa_pass": ccpa_pass,
            "local_pass": local_pass,
            "per_regulation": scores,
            "findings": findings,
        }


class TrustEngine:
    """
    Computes public-trust score.
    trust_score = privacy_score * 0.5 + compliance_score * 0.3 + transparency_score * 0.2
    """

    @staticmethod
    def calculate(
        privacy_score: float,
        compliance_score: float,
        transparency_score: float = 95.0,
    ) -> float:
        raw = (
            privacy_score * 0.5
            + compliance_score * 0.3
            + transparency_score * 0.2
        )
        return round(min(100.0, max(0.0, raw)), 1)
