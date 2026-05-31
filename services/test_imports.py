import importlib
import sys

modules = [
    "services.auth_service.main",
    "services.camera_service.main",
    "services.vision_service.main",
    "services.privacy_service.main",
    "services.event_service.main",
    "services.audit_service.main",
    "services.analytics_service.main",
    "services.simulator_service.main",
    "services.identity_governance_service.main",
    "services.gateway",
]

print("Verifying microservice module imports...")
success = True
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"  [OK]  {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")
        success = False

if success:
    print("All imports verified successfully.")
    sys.exit(0)
else:
    print("Some imports failed. Fix errors above.")
    sys.exit(1)
