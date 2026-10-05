
import sys, json, subprocess, time, os
sys.path.insert(0, os.path.dirname("/data/data/com.termux/files/home/Agentes-Maestros-audit/__vertical_slice_api__.py"))

# Read and compile the API code
code = open("/data/data/com.termux/files/home/Agentes-Maestros-audit/__vertical_slice_api__.py").read()
compiled = compile(code, "/data/data/com.termux/files/home/Agentes-Maestros-audit/__vertical_slice_api__.py", "exec")

# Create namespace and execute
ns = {}
exec(compiled, ns)

# Get the app
app = ns['app']

# Test the health endpoint directly without starting server
with app.test_client() as client:
    resp = client.get("/health")
    print(json.dumps({"status_code": resp.status_code, "body": resp.get_json()}))
