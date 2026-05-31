"""
BlindWatch Risk Engine
-----------------------
Computes composite risk scores per anonymous entity based on:
  - Movement behaviour
  - Zone violations
  - Object interactions
  - Anomaly deviation
  - Crowd density signals
  - Weapon detections

Formula:
  risk_score = (
      0.20 * movement_score +
      0.25 * zone_score     +
      0.20 * object_score   +
      0.15 * anomaly_score  +
      0.10 * crowd_score    +
      0.10 * weapon_score
  ) * 100
"""
from typing import Dict, Optional


RISK_WEIGHTS = {
    "movement": 0.20,
    "zone":     0.25,
    "object":   0.20,
    "anomaly":  0.15,
    "crowd":    0.10,
    "weapon":   0.10,
}

RISK_LABELS = {
    "LOW":      (0,  30),
    "MEDIUM":   (31, 60),
    "HIGH":     (61, 80),
    "CRITICAL": (81, 100),
}


def _classify(score: float) -> str:
    for label, (lo, hi) in RISK_LABELS.items():
        if lo <= score <= hi:
            return label
    return "CRITICAL"


class RiskEngine:
    """
    Computes normalised risk score (0–100) and risk level label.
    All input sub-scores are expected in the range 0.0–1.0.
    """

    @staticmethod
    def calculate(
        movement_score: float = 0.0,
        zone_score:     float = 0.0,
        object_score:   float = 0.0,
        anomaly_score:  float = 0.0,
        crowd_score:    float = 0.0,
        weapon_score:   float = 0.0,
    ) -> Dict:
        raw = (
            RISK_WEIGHTS["movement"] * movement_score +
            RISK_WEIGHTS["zone"]     * zone_score     +
            RISK_WEIGHTS["object"]   * object_score   +
            RISK_WEIGHTS["anomaly"]  * anomaly_score  +
            RISK_WEIGHTS["crowd"]    * crowd_score     +
            RISK_WEIGHTS["weapon"]   * weapon_score
        )
        score = round(min(100.0, max(0.0, raw * 100)), 1)
        return {
            "risk_score": score,
            "risk_level": _classify(score),
            "components": {
                "movement": round(movement_score * 100, 1),
                "zone":     round(zone_score     * 100, 1),
                "object":   round(object_score   * 100, 1),
                "anomaly":  round(anomaly_score  * 100, 1),
                "crowd":    round(crowd_score    * 100, 1),
                "weapon":   round(weapon_score   * 100, 1),
            },
        }


class MovementEngine:
    """
    Derives movement sub-score from entity trajectory data.
    Calculates: speed, direction, distance, zone transitions.
    """

    NORMAL_SPEED_MAX = 2.0   # m/s – above this triggers elevated score
    SPRINT_SPEED     = 5.0   # m/s – maximum expected sprint

    @staticmethod
    def calculate(
        current_speed: float = 0.0,         # m/s
        direction_changes: int = 0,          # sharp turns in last 30s
        is_stationary_prolonged: bool = False,
        zone_exit_count: int = 0,
    ) -> Dict:
        # Speed sub-score: 0 (slow/normal) → 1 (sprint)
        speed_score = min(1.0, max(0.0, (current_speed - MovementEngine.NORMAL_SPEED_MAX) / MovementEngine.SPRINT_SPEED))
        # Erratic turning score
        erratic_score = min(1.0, direction_changes / 10.0)
        # Prolonged stationary (possible lurking)
        stationary_score = 0.5 if is_stationary_prolonged else 0.0
        # Repeated zone exits are suspicious
        zone_score = min(1.0, zone_exit_count / 5.0)

        movement_score = (speed_score * 0.40 + erratic_score * 0.30 + stationary_score * 0.15 + zone_score * 0.15)
        return {
            "movement_score": round(movement_score, 3),
            "speed_ms": round(current_speed, 2),
            "direction_changes": direction_changes,
            "is_stationary_prolonged": is_stationary_prolonged,
        }

    @staticmethod
    def compute_speed(prev_pos: tuple, curr_pos: tuple, fps: float) -> float:
        """Pixel-space Euclidean speed approximation."""
        if fps == 0:
            return 0.0
        dx = curr_pos[0] - prev_pos[0]
        dy = curr_pos[1] - prev_pos[1]
        dist = (dx ** 2 + dy ** 2) ** 0.5
        return round(dist / fps, 2)

    @staticmethod
    def compute_direction(prev_pos: tuple, curr_pos: tuple) -> str:
        dx = curr_pos[0] - prev_pos[0]
        dy = curr_pos[1] - prev_pos[1]
        if abs(dx) < 5 and abs(dy) < 5:
            return "STATIONARY"
        if abs(dx) > abs(dy):
            return "EAST" if dx > 0 else "WEST"
        return "SOUTH" if dy > 0 else "NORTH"


class ZoneEngine:
    """
    Evaluates entity position against configured zone rules.
    Zones carry types: 'safe' | 'restricted' | 'critical'
    """

    ZONE_PENALTIES = {
        "safe":       0.0,
        "restricted": 0.7,
        "critical":   1.0,
    }

    @staticmethod
    def evaluate(entity_x: float, entity_y: float, zones: list) -> Dict:
        """
        zones: list of dicts
          { id, name, zone_type, x1, y1, x2, y2 }
        """
        violations = []
        max_penalty = 0.0
        for zone in zones:
            zx1, zy1 = zone.get("x1", 0), zone.get("y1", 0)
            zx2, zy2 = zone.get("x2", 9999), zone.get("y2", 9999)
            if zx1 <= entity_x <= zx2 and zy1 <= entity_y <= zy2:
                penalty = ZoneEngine.ZONE_PENALTIES.get(zone.get("zone_type", "safe"), 0.0)
                if penalty > 0:
                    violations.append({
                        "zone_id":   zone.get("id"),
                        "zone_name": zone.get("name"),
                        "zone_type": zone.get("zone_type"),
                        "penalty":   penalty,
                    })
                max_penalty = max(max_penalty, penalty)
        return {
            "zone_score":  round(max_penalty, 3),
            "violations":  violations,
            "in_violation": len(violations) > 0,
        }


class ObjectInteractionEngine:
    """
    Scores object interaction events (pick-up, drop, disappear).
    """
    INTERACTION_WEIGHTS = {
        "PICKED_UP_OBJECT":  0.3,
        "LEFT_OBJECT":       0.4,
        "REMOVED_OBJECT":    0.7,
        "CARRIED_WEAPON":    1.0,
    }

    @staticmethod
    def score(interactions: list) -> float:
        """interactions: list of interaction type strings."""
        if not interactions:
            return 0.0
        return min(1.0, max(ObjectInteractionEngine.INTERACTION_WEIGHTS.get(i, 0.2) for i in interactions))


class CrowdAnalysisEngine:
    """
    Estimates crowd density and detects panic/stampede events.
    """
    @staticmethod
    def calculate(people_count: int, area_sq_m: float = 100.0) -> Dict:
        density = people_count / max(1, area_sq_m)  # people/m²
        if density >= 2.0:
            level, crowd_score = "PANIC", 1.0
        elif density >= 1.0:
            level, crowd_score = "CONGESTED", 0.7
        elif density >= 0.5:
            level, crowd_score = "DENSE", 0.4
        elif density >= 0.1:
            level, crowd_score = "MODERATE", 0.15
        else:
            level, crowd_score = "SPARSE", 0.0

        return {
            "people_count":   people_count,
            "density":        round(density, 3),
            "density_level":  level,
            "crowd_score":    round(crowd_score, 3),
        }


class AnomalyEngine:
    """
    Detects anomalous behaviour by comparing observed vs. baseline statistics.
    anomaly_score = weighted_deviation (normalised 0→1)
    """

    @staticmethod
    def calculate(
        speed_deviation: float = 0.0,
        path_deviation: float = 0.0,
        dwell_deviation: float = 0.0,
        zone_access_deviation: float = 0.0,
        object_interaction_deviation: float = 0.0,
    ) -> Dict:
        """All deviation inputs expected 0.0–1.0."""
        weights = [0.25, 0.25, 0.20, 0.15, 0.15]
        devs    = [speed_deviation, path_deviation, dwell_deviation,
                   zone_access_deviation, object_interaction_deviation]
        anomaly_score = round(sum(w * d for w, d in zip(weights, devs)), 3)
        return {
            "anomaly_score": min(1.0, anomaly_score),
            "is_anomalous":  anomaly_score > 0.5,
        }
