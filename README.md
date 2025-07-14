ag: Ask Gpt, or AGent

useful scripts

```bash
uv run -m agent.cli

uv build
uv tool install dist/ag-0.1.0-py3-none-any.whl

cat .env | xargs -I {} echo 'export' {} > .env.bash
source .env.bash

ag
```