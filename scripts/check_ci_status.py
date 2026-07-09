import json, urllib.request

url = 'https://api.github.com/repos/Universidad-de-Lima/survey-storytelling/actions/workflows/135624485/runs?per_page=5'
req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})
data = json.loads(urllib.request.urlopen(req).read().decode())

for run in data.get('workflow_runs', []):
    hc = run.get('head_commit', {}) or {}
    print(f"SHA: {run['head_sha'][:8]}")
    print(f"  Evento: {run['event']}")
    print(f"  Status: {run['status']}")
    print(f"  Conclusion: {run['conclusion']}")
    print(f"  Branch: {run['head_branch']}")
    msg = hc.get('message', 'N/A')
    print(f"  Msg: {msg[:60]}")
    print()
