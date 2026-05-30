from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import SimulationResult
from backend.engines.audit import AuditEngine

class SimulatorEngine:
    @staticmethod
    def run_simulation(
        db: Session,
        config_name: str,
        cameras_count: int,
        retention_days: int,
        sensitivity: float, # 0.0 to 1.0
        identity_collection: str, # "default_anonymized", "stored_by_default"
        crowd_density: str, # "low", "medium", "high"
        threat_level: str,  # "low", "medium", "high"
        user_id: int = None,
        username: str = None,
        role: str = None
    ) -> dict:
        """
        Runs the simulation scoring matrix for security and privacy trade-offs.
        Returns a side-by-side analysis contrasting Traditional CCTV with BlindWatch AI.
        """
        # --- BlindWatch AI Calculations ---
        # Safety Score: Increases with cameras, sensitivity, threat_level, crowd density
        safety_base = 40.0
        safety_cams = min(cameras_count * 2.5, 30.0)
        safety_sens = sensitivity * 20.0
        safety_threat = 10.0 if threat_level == "low" else (20.0 if threat_level == "medium" else 30.0)
        bw_safety = min(safety_base + safety_cams + safety_sens + safety_threat, 98.0)
        
        # Privacy Score: Depends on identity collection and retention days
        privacy_base = 98.0
        if identity_collection == "stored_by_default":
            privacy_base -= 50.0
        # Longer retention reduces privacy score slightly due to storage surface area
        retention_penalty = min(retention_days * 0.4, 25.0)
        # Higher camera counts reduce privacy slightly due to aggregate data surface
        camera_penalty = min(cameras_count * 0.15, 8.0)
        bw_privacy = max(privacy_base - retention_penalty - camera_penalty, 30.0)
        
        # Trust Score: Function of privacy and explainability
        bw_trust = min(bw_privacy * 0.8 + bw_safety * 0.2, 99.0)
        
        # Compliance Score: Evaluates legal status (GDPR, CCPA)
        bw_compliance = 99.0
        if identity_collection == "stored_by_default":
            bw_compliance -= 45.0
        if retention_days > 30:
            bw_compliance -= min((retention_days - 30) * 0.5, 20.0)
        bw_compliance = max(bw_compliance, 35.0)
        
        # False Positive Rate: Increases with sensitivity
        bw_fpr = min((sensitivity ** 2) * 15.0 + (5.0 if crowd_density == "high" else 1.0), 35.0)
        
        # Bias Risk: In BlindWatch, identity/demographics are obscured, keeping bias extremely low
        bw_bias = min(3.0 + (sensitivity * 2.0), 10.0)
        
        # --- Traditional CCTV Calculations ---
        # Safety: Marginally lower because search indexing is reactive and lacks active behavior modeling
        trad_safety = max(bw_safety - 10.0, 30.0)
        
        # Privacy: Extremely low because all faces and tracks are captured and stored in cleartext by default
        trad_privacy = max(20.0 - (retention_days * 0.3) - (cameras_count * 0.1), 5.0)
        
        # Trust: Low due to risk of leaks, rogue tracking, and lack of transparency
        trad_trust = max(15.0 - (retention_days * 0.1), 8.0)
        
        # Compliance: Violates GDPR by default due to mass biometric capture without consent
        trad_compliance = max(10.0 if retention_days > 14 else 25.0, 5.0)
        
        # False Positive Rate: Moderate
        trad_fpr = min((sensitivity * 12.0) + 8.0, 40.0)
        
        # Bias Risk: Extremely high due to face identification models trained on biased datasets
        trad_bias = min(45.0 + (sensitivity * 20.0), 85.0)
        
        # Create DB record for the simulation
        result = SimulationResult(
            timestamp=datetime.utcnow(),
            config_name=config_name,
            cameras_count=cameras_count,
            retention_days=retention_days,
            sensitivity=sensitivity,
            identity_collection=identity_collection,
            crowd_density=crowd_density,
            threat_level=threat_level,
            safety_score=bw_safety,
            privacy_score=bw_privacy,
            trust_score=bw_trust,
            compliance_score=bw_compliance,
            false_positive_rate=bw_fpr,
            bias_risk=bw_bias
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        
        # Log this simulation audit
        AuditEngine.log_action(
            db=db,
            action="SIMULATION_RUN",
            reason=f"Executed threat-privacy trade-off model: {config_name}",
            outcome="success",
            user_id=user_id,
            username=username,
            role=role
        )
        
        return {
            "simulation_id": result.id,
            "config_name": config_name,
            "blindwatch": {
                "safety_score": round(bw_safety, 1),
                "privacy_score": round(bw_privacy, 1),
                "trust_score": round(bw_trust, 1),
                "compliance_score": round(bw_compliance, 1),
                "false_positive_rate": round(bw_fpr, 1),
                "bias_risk": round(bw_bias, 1)
            },
            "traditional": {
                "safety_score": round(trad_safety, 1),
                "privacy_score": round(trad_privacy, 1),
                "trust_score": round(trad_trust, 1),
                "compliance_score": round(trad_compliance, 1),
                "false_positive_rate": round(trad_fpr, 1),
                "bias_risk": round(trad_bias, 1)
            }
        }
