from backend.app import create_app
import urllib.parse

app = create_app()
print("\n--- Registered Routes ---")
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods)
    print(f"{rule.endpoint:50s} {methods:20s} {rule}")
print("--------------------------\n")
