import urllib.request
import urllib.error
import json

targets = [
    ("Auth Service", 8001, "healthz"),
    ("Camera Service", 8002, "api/cameras"),
    ("Vision Service", 8003, "api/entities"),
    ("Privacy Service", 8004, "api/privacy-metrics"),
    ("Event Service", 8005, "api/events"),
    ("Audit Service", 8006, "api/audit-logs"),
    ("Analytics Service", 8007, "api/analytics"),
    ("Simulator Service", 8008, "api/simulator/results"),
    ("Governance Service", 8009, "api/identity-requests"),
    ("API Gateway", 8000, "healthz")
]

print("Scanning microservice health and endpoints...")
for name, port, path in targets:
    url = f"http://127.0.0.1:{port}/{path}"
    try:
        req = urllib.request.Request(url)
        # Auth Service token endpoint won't require auth for /healthz, but others might.
        # Let's inspect the status code
        res = urllib.request.urlopen(req, timeout=10.0)
        print(f"  [OK]  {name} on port {port}: HTTP {res.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {name} on port {port} (Path: /{path})")
        # Read error response
        try:
            print(f"        Detail: {e.read().decode()}")
        except Exception:
            pass
    except Exception as e:
        print(f"  [ERR] {name} on port {port}: {e}")
