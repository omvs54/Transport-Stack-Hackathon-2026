import os
import re
import urllib.request
import json

def check_secrets():
    print("=== 1. Checking for exposed API keys or secrets ===")
    pattern = re.compile(r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{8,}["\']')
    found = []
    base = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(base):
        if "__pycache__" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith((".py", ".json", ".md", ".html", ".bat", ".txt")):
                if f in [".env.example", "test_live.py"]:
                    continue
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                    for i, line in enumerate(fp, 1):
                        if pattern.search(line):
                            found.append((os.path.relpath(path, base), i, line.strip()))
    if not found:
        print("[SUCCESS] Zero hardcoded secrets found! All keys are safely environment-managed.")
    else:
        print(f"[WARNING] Found {len(found)} possible secrets:")
        for p, line, text in found:
            print(f"  {p}:{line} -> {text}")
    return len(found) == 0

def check_live_server():
    print("\n=== 2. Verifying live prototype server on http://localhost:5000 ===")
    base_url = "http://127.0.0.1:5000"
    
    # Check index
    try:
        with urllib.request.urlopen(f"{base_url}/", timeout=3) as resp:
            html = resp.read().decode("utf-8")
            assert "Delhi Bus Crowdedness-Aware Journey Planner" in html
            assert "FACC15" in html  # Caution Yellow
            assert "18181B" in html  # Asphalt Charcoal
            print(f"[SUCCESS] GET / returned 200 OK with Industrial Palette.")
    except Exception as e:
        print(f"[FAIL] GET / failed: {e}")
        return False
        
    # Check stops
    try:
        with urllib.request.urlopen(f"{base_url}/api/stops", timeout=3) as resp:
            stops = json.loads(resp.read().decode("utf-8"))
            assert len(stops) > 50
            assert "Anand Vihar ISBT" in stops
            assert "Connaught Place" in stops
            print(f"[SUCCESS] GET /api/stops returned {len(stops)} stops (including Anand Vihar ISBT & Connaught Place).")
    except Exception as e:
        print(f"[FAIL] GET /api/stops failed: {e}")
        return False

    # Check Anand Vihar to Connaught Place
    try:
        url = f"{base_url}/api/options?from=Anand+Vihar+ISBT&to=Connaught+Place&depart=18:00&day=weekday"
        with urllib.request.urlopen(url, timeout=3) as resp:
            opts = json.loads(resp.read().decode("utf-8"))
            assert len(opts) > 0
            print(f"[SUCCESS] GET /api/options (Anand Vihar -> Connaught Place, 18:00) returned {len(opts)} options:")
            for o in opts[:3]:
                print(f"   * Route {o['route']} | Dep {o['depart']} | {o['minutes']} min | Level: {o['level_label']} | Worst: {o['worst_stretch']}")
    except Exception as e:
        print(f"[FAIL] GET /api/options failed: {e}")
        return False

    return True

if __name__ == "__main__":
    s_ok = check_secrets()
    l_ok = check_live_server()
    if s_ok and l_ok:
        print("\n>>> ALL CHECKS PASSED: Ready for GitHub and live presentation! <<<")
