import subprocess
import sys
import time
import os

SERVICES = [
    ("Auth Service", "services.auth_service.main:app", 8001),
    ("Camera Service", "services.camera_service.main:app", 8002),
    ("Vision Service", "services.vision_service.main:app", 8003),
    ("Privacy Service", "services.privacy_service.main:app", 8004),
    ("Event Service", "services.event_service.main:app", 8005),
    ("Audit Service", "services.audit_service.main:app", 8006),
    ("Analytics Service", "services.analytics_service.main:app", 8007),
    ("Simulator Service", "services.simulator_service.main:app", 8008),
    ("Identity Governance Service", "services.identity_governance_service.main:app", 8009),
    ("API Gateway", "services.gateway:app", 8000),
]

def main():
    print("=" * 60)
    print("       BlindWatch AI OS Modular Microservices Manager        ")
    print("=" * 60)
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    processes = []
    
    try:
        for name, module, port in SERVICES:
            print(f"Launching {name} on port {port}...")
            
            # For cloud deployment (Render/Heroku), the API Gateway must bind to 0.0.0.0 and use the provided PORT.
            # Internal microservices can remain on 127.0.0.1
            host = "0.0.0.0" if name == "API Gateway" else "127.0.0.1"
            actual_port = os.environ.get("PORT", str(port)) if name == "API Gateway" else str(port)

            cmd = [
                sys.executable, "-m", "uvicorn", module,
                "--host", host,
                "--port", actual_port,
                "--log-level", "warning"
            ]
            p = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            processes.append((name, p))
            time.sleep(0.5) # staggered startup
            
        print("\nAll modular microservices launched successfully!")
        gateway_port = os.environ.get("PORT", "8000")
        print(f"API Gateway entrypoint is listening on: http://0.0.0.0:{gateway_port}")
        print("Press Ctrl+C to terminate all services.\n")
        
        while True:
            # Check processes health
            for name, p in processes:
                if p.poll() is not None:
                    # Process died
                    out, _ = p.communicate()
                    print(f"\n[ALERT] {name} has stopped (Exit code: {p.returncode})")
                    print(f"Output:\n{out}")
                    raise SystemExit(1)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTerminating all services gracefully...")
    finally:
        for name, p in processes:
            print(f"Stopping {name}...")
            p.terminate()
            p.wait()
        print("Cleanup complete. All services stopped.")

if __name__ == "__main__":
    main()
