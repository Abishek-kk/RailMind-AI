from pathlib import Path

agent_files = [
    Path("f:/teamaccelerate/backend/app/agents/perception_agent.py"),
    Path("f:/teamaccelerate/backend/app/agents/intervention_agent.py"),
]

for path in agent_files:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        path.write_bytes(data[3:])
        print(f"stripped BOM from {path}")
    else:
        print(f"no BOM in {path}")

wheel_files = [
    Path("f:/teamaccelerate/backend/pydantic_core-2.47.0-cp314-cp314-win_amd64.whl"),
    Path("f:/teamaccelerate/backend/typing_extensions-4.15.0-py3-none-any.whl"),
]
for path in wheel_files:
    if path.exists():
        path.unlink()
        print(f"deleted {path}")
    else:
        print(f"missing {path}")
