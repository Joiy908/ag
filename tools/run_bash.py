import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="aws-tools", host='0.0.0.0', port='9000')

@mcp.tool()
def run_bash_script(script: str) -> tuple[str,str]:
    """run a bash script string and return (stdout, stderr)."""
    result = subprocess.run(
            ['bash','-c',script],
            capture_output=True,
            text=True
    )
    return result.stdout.strip(), result.stderr.strip()


if __name__ == '__main__':
    mcp.run(transport='streamable-http')
