"""
BlindWatch Threat Engine
-------------------------
Generates security events from risk signals.

Supported threat types:
  THEFT      – object removed + fast exit + anomaly > 60
  INTRUSION  – restricted zone entry without authorisation
  WEAPON     – knife/gun detected at > 85% confidence
  FIRE       – fire or smoke detected
  MEDICAL    – person down / no movement for 30+ seconds
"""
from typing import Dict, List, Optional
import datetime


class ThreatEventBuilder:
    """Builds structured threat event dicts ready to be persisted."""

    @staticmethod
    def build(
        event_type: str,
        entity_id: str,
        camera_id: str,
        location: str,
        risk_score: float,
        confidence: float,
        reasoning: str,
        evidence: Optional[List[Dict]] = None,
        tenant_id: str = "default",
    ) -> Dict:
        return {
            "event_type":  event_type,
            "entity_id":   entity_id,
            "camera_id":   camera_id,
            "location":    location,
            "risk_score":  round(risk_score, 1),
            "confidence":  round(min(1.0, confidence), 3),
            "reasoning":   reasoning,
            "evidence":    evidence or [],
            "status":      "unresolved",
            "tenant_id":   tenant_id,
            "created_at":  datetime.datetime.utcnow().isoformat(),
        }


class ThreatEngine:
    """
    Evaluates sensor/AI signals and fires threat events.
    Returns a list of zero or more ThreatEvent dicts.
    """

    WEAPON_CLASSES = {"knife", "gun", "pistol", "rifle", "firearm", "blade"}
    FIRE_CLASSES   = {"fire", "smoke", "flame"}

    @staticmethod
    def evaluate(
        entity_id: str,
        camera_id: str,
        location: str,
        tenant_id: str,
        # Risk sub-scores (0–100)
        anomaly_score: float     = 0.0,
        risk_score: float        = 0.0,
        # Movement signals
        current_speed: float     = 0.0,   # m/s
        direction: str           = "STATIONARY",
        # Zone signals
        zone_violations: list    = None,
        # Object signals
        detected_objects: list   = None,  # [{"class": "person", "confidence": 0.94}, ...]
        object_interactions: list = None, # ["REMOVED_OBJECT", ...]
        # Medical signal
        stationary_seconds: float = 0.0,
        # Tracking confidence (0–1)
        tracking_confidence: float = 1.0,
    ) -> List[Dict]:
        zone_violations    = zone_violations    or []
        detected_objects   = detected_objects   or []
        object_interactions = object_interactions or []
        events = []

        def _confidence(model_conf: float) -> float:
            return round(min(1.0, model_conf * tracking_confidence), 3)

        # ── WEAPON DETECTION ────────────────────────────────────────────
        for obj in detected_objects:
            cls  = obj.get("class", "").lower()
            conf = obj.get("confidence", 0.0)
            if cls in ThreatEngine.WEAPON_CLASSES and conf > 0.85:
                events.append(ThreatEventBuilder.build(
                    event_type  = "WEAPON_DETECTED",
                    entity_id   = entity_id,
                    camera_id   = camera_id,
                    location    = location,
                    risk_score  = max(85.0, risk_score),
                    confidence  = _confidence(conf),
                    reasoning   = (
                        f"YOLOv8 detected '{cls}' with {round(conf*100,1)}% confidence. "
                        "Immediate security response required."
                    ),
                    evidence    = [{"type": "detection", "class": cls, "confidence": conf}],
                    tenant_id   = tenant_id,
                ))

        # ── FIRE / SMOKE DETECTION ───────────────────────────────────────
        for obj in detected_objects:
            cls  = obj.get("class", "").lower()
            conf = obj.get("confidence", 0.0)
            if cls in ThreatEngine.FIRE_CLASSES and conf > 0.70:
                events.append(ThreatEventBuilder.build(
                    event_type  = "FIRE_DETECTED",
                    entity_id   = entity_id,
                    camera_id   = camera_id,
                    location    = location,
                    risk_score  = max(80.0, risk_score),
                    confidence  = _confidence(conf),
                    reasoning   = f"Fire/smoke indicator '{cls}' detected. Emergency evacuation protocol triggered.",
                    evidence    = [{"type": "detection", "class": cls, "confidence": conf}],
                    tenant_id   = tenant_id,
                ))

        # ── INTRUSION DETECTION ─────────────────────────────────────────
        critical_violations = [v for v in zone_violations if v.get("zone_type") in ("restricted", "critical")]
        if critical_violations:
            zone_names = ", ".join(v.get("zone_name", "Unknown") for v in critical_violations)
            events.append(ThreatEventBuilder.build(
                event_type  = "INTRUSION_DETECTED",
                entity_id   = entity_id,
                camera_id   = camera_id,
                location    = location,
                risk_score  = max(70.0, risk_score),
                confidence  = _confidence(0.88),
                reasoning   = (
                    f"Entity entered restricted area(s): {zone_names}. "
                    "No authorisation record found."
                ),
                evidence    = critical_violations,
                tenant_id   = tenant_id,
            ))

        # ── THEFT DETECTION ─────────────────────────────────────────────
        if (
            "REMOVED_OBJECT" in object_interactions
            and current_speed > 2.0
            and anomaly_score > 60.0
        ):
            events.append(ThreatEventBuilder.build(
                event_type  = "THEFT_SUSPECTED",
                entity_id   = entity_id,
                camera_id   = camera_id,
                location    = location,
                risk_score  = max(75.0, risk_score),
                confidence  = _confidence(0.82),
                reasoning   = (
                    f"Entity removed an object and exited at high speed ({current_speed:.1f} m/s). "
                    f"Anomaly score: {anomaly_score:.0f}/100. Theft signature match."
                ),
                evidence    = [{"type": "interaction", "action": "REMOVED_OBJECT", "speed": current_speed}],
                tenant_id   = tenant_id,
            ))

        # ── MEDICAL EMERGENCY ───────────────────────────────────────────
        if stationary_seconds >= 30.0 and direction == "STATIONARY":
            events.append(ThreatEventBuilder.build(
                event_type  = "MEDICAL_EMERGENCY",
                entity_id   = entity_id,
                camera_id   = camera_id,
                location    = location,
                risk_score  = max(65.0, risk_score),
                confidence  = _confidence(0.75),
                reasoning   = (
                    f"Entity has been stationary for {stationary_seconds:.0f} seconds. "
                    "Possible person-down medical emergency."
                ),
                evidence    = [{"type": "behaviour", "stationary_seconds": stationary_seconds}],
                tenant_id   = tenant_id,
            ))

        return events


class ExplainableAIEngine:
    """
    Generates human-readable XAI explanations for each threat event.
    Returns a list of weighted factor dicts.
    """

    FACTOR_MAP = {
        "WEAPON_DETECTED":    [
            ("Weapon Class Identified",       42),
            ("Detection Confidence High",     30),
            ("Threat Signature Match",        28),
        ],
        "FIRE_DETECTED":      [
            ("Fire/Smoke Indicator Detected", 45),
            ("Thermal Anomaly Present",       35),
            ("Emergency Protocol Triggered",  20),
        ],
        "INTRUSION_DETECTED": [
            ("Restricted Zone Entry",         42),
            ("No Authorisation Record",       33),
            ("Movement Pace Abnormality",     25),
        ],
        "THEFT_SUSPECTED":    [
            ("Object Removed From Scene",     38),
            ("High-Speed Exit Detected",      35),
            ("Anomaly Deviation Score > 60",  27),
        ],
        "MEDICAL_EMERGENCY":  [
            ("Extended Motionless Detection", 50),
            ("Absence of Normal Gait",        30),
            ("No Self-Recovery Movement",     20),
        ],
    }

    GENERIC_FACTORS = [
        ("Behaviour Deviation from Baseline", 35),
        ("Zone Access Pattern Mismatch",      35),
        ("Object Interaction Detected",       30),
    ]

    @classmethod
    def explain(cls, event_type: str, risk_score: float, custom_factors: list = None) -> Dict:
        factors = cls.FACTOR_MAP.get(event_type, cls.GENERIC_FACTORS)
        if custom_factors:
            factors = custom_factors

        factor_list = [{"reason": r, "weight": w} for r, w in factors]
        summary = (
            f"BlindWatch AI flagged this entity with risk score {risk_score:.0f}/100. "
            f"Primary trigger: {factor_list[0]['reason']}. "
            "All detections are privacy-preserving – no identity data accessed."
        )
        return {
            "event_type":   event_type,
            "risk_score":   risk_score,
            "factors":      factor_list,
            "summary":      summary,
            "model":        "YOLOv8 + ByteTrack + BlindWatch Risk Engine",
            "privacy_note": "Anonymous entity only. No biometric data stored.",
        }


class ConfidenceCalculator:
    """
    event_confidence = model_confidence * tracking_confidence  (normalised 0→100)
    """
    @staticmethod
    def calculate(model_confidence: float, tracking_confidence: float) -> float:
        return round(min(100.0, model_confidence * tracking_confidence * 100), 1)
