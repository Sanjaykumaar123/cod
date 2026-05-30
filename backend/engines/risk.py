from typing import Dict, List, Tuple

class RiskScoringEngine:
    @staticmethod
    def calculate_risk(
        movement_anomaly: bool,
        restricted_zone_access: bool,
        object_interaction: str, # "none", "bag_left_behind", "weapon_held", etc.
        weapon_detected: bool,
        crowd_anomaly: bool,
        base_speed: float = 1.0 # m/s
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates a dynamic risk score from 0 to 100 based on threats and behavior.
        Returns the overall score and the contributing weights for Explainable AI.
        """
        score = 5.0  # Base line noise risk
        factors = {}
        
        if weapon_detected:
            score += 75.0
            factors["Weapon Detection (Type: Lethal Threat)"] = 75.0
            
        if restricted_zone_access:
            score += 35.0
            factors["Unauthorized Access (Restricted Area)"] = 35.0
            
        if object_interaction == "bag_left_behind":
            score += 25.0
            factors["Unattended Object (Possible Security Hazard)"] = 25.0
        elif object_interaction == "weapon_held" and not weapon_detected:
            score += 55.0
            factors["Suspect Object Interaction"] = 55.0
            
        if movement_anomaly or base_speed > 3.5: # Running speed
            score += 20.0
            factors["Movement Anomaly (Sudden Velocity Spike)"] = 20.0
            
        if crowd_anomaly:
            score += 30.0
            factors["Crowd Anomaly (Dispersal/Panic Signature)"] = 30.0
            
        # Ensure we cap the score at 100.0 and floor it at 0.0
        final_score = min(max(score, 0.0), 100.0)
        
        # Normalize weights to add up to the risk score, or express them as raw contribution
        return final_score, factors
