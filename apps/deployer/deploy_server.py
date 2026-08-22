import json
import os
import shutil
import subprocess
import tarfile
import threading
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPOSITORY = Path(os.environ.get("DEPLOY_REPOSITORY", "/workspace")).resolve()
TOKEN = os.environ.get("DEPLOY_SERVICE_TOKEN", "")
COMPOSE_PROJECT_NAME = os.environ.get("DEPLOY_COMPOSE_PROJECT_NAME", "supertools")
MAX_LOG_CHARS = 30_000
lock = threading.Lock()
state: dict[str, object] = {
    "status": "idle",
    "target": None,
    "startedAt": None,
    "finishedAt": None,
    "log": "",
}


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def append_log(message: str) -> None:
    state["log"] = (str(state["log"]) + message)[-MAX_LOG_CHARS:]


def run_deployment(target: str) -> None:
    compose = [
        "docker",
        "compose",
        "--project-name",
        COMPOSE_PROJECT_NAME,
        "--env-file",
        ".env.production",
    ]
    commands = [
        ["git", "pull", "--ff-only"],
    ]
    try:
        for command in commands:
            run_command(command)

        build_args = deployment_build_args()
        if target == "admin":
            build_admin(build_args)
        else:
            run_command([*compose, "build", *build_args, "server"])

        run_command(
            [
                *compose,
                "up",
                "-d",
                "--no-deps",
                "--remove-orphans",
                target,
            ]
        )
        if target == "server":
            wait_for_api(compose)
        else:
            wait_for_admin(compose)
        run_command([*compose, "ps", target])
        state["status"] = "succeeded"
    except (OSError, RuntimeError) as error:
        append_log(f"\nERROR: {error}\n")
        state["status"] = "failed"
    finally:
        state["finishedAt"] = timestamp()
        lock.release()


def deployment_build_args() -> list[str]:
    revision = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    deployed_at = timestamp()
    append_log(f"\nRelease: {revision} at {deployed_at}\n")
    return [
        "--build-arg",
        f"APP_VERSION={revision}",
        "--build-arg",
        f"APP_DEPLOYED_AT={deployed_at}",
    ]


def run_command(command: list[str]) -> None:
    append_log(f"\n$ {' '.join(command)}\n")
    process = subprocess.Popen(
        command,
        cwd=REPOSITORY,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        append_log(line)
        print(line, end="", flush=True)
    if process.wait() != 0:
        raise RuntimeError(f"命令执行失败（退出码 {process.returncode}）")


def build_admin(build_args: list[str]) -> None:
    suffix = f"{os.getpid()}-{int(time.time())}"
    container = f"supertools-admin-build-{suffix}"
    dist = REPOSITORY / "apps/admin/dist"
    try:
        run_command(
            [
                "docker",
                "run",
                "-d",
                "--name",
                container,
                "--tmpfs",
                "/workspace:exec,size=1073741824",
                "--add-host",
                "host.docker.internal:host-gateway",
                *proxy_environment_args(),
                "-w",
                "/workspace",
                "node:22-alpine",
                "sleep",
                "infinity",
            ]
        )
        run_command(
            ["docker", "exec", container, "mkdir", "-p", "/workspace/apps/miniapp"]
        )
        copy_admin_context(container)
        run_command(
            [
                "docker",
                "exec",
                container,
                "sh",
                "-lc",
                (
                    "export HOME=/workspace/.home "
                    "XDG_CACHE_HOME=/workspace/.cache "
                    "XDG_CONFIG_HOME=/workspace/.config && "
                    "cd apps/admin && "
                    "npm install --ignore-scripts --no-package-lock "
                    "--no-audit --no-fund && "
                    "npm run build"
                ),
            ]
        )
        if dist.exists():
            shutil.rmtree(dist)
        copy_admin_dist(container, dist.parent)
        run_command(
            [
                "docker",
                "build",
                *build_args,
                "-f",
                "apps/admin/Dockerfile.runtime",
                "-t",
                "supertools-admin:latest",
                ".",
            ]
        )
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)


def proxy_environment_args() -> list[str]:
    args: list[str] = []
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"):
        value = os.environ.get(name, "").strip()
        if value:
            args.extend(["--env", f"{name}={value}"])
    return args


def copy_admin_context(container: str) -> None:
    process = subprocess.Popen(
        ["docker", "exec", "-i", container, "tar", "-x", "-C", "/workspace"],
        stdin=subprocess.PIPE,
        cwd=REPOSITORY,
    )
    assert process.stdin is not None
    with tarfile.open(fileobj=process.stdin, mode="w|") as archive:
        for path in ("package.json", "pnpm-workspace.yaml", "pnpm-lock.yaml"):
            archive.add(REPOSITORY / path, arcname=path)
        archive.add(
            REPOSITORY / "apps/admin",
            arcname="apps/admin",
            filter=admin_source_filter,
        )
        archive.add(
            REPOSITORY / "apps/miniapp/package.json",
            arcname="apps/miniapp/package.json",
        )
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("复制管理端构建上下文失败")


def admin_source_filter(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    parts = Path(info.name).parts
    if "node_modules" in parts or "dist" in parts:
        return None
    return info


def copy_admin_dist(container: str, destination: Path) -> None:
    process = subprocess.Popen(
        [
            "docker",
            "exec",
            container,
            "tar",
            "-c",
            "-C",
            "/workspace/apps/admin",
            "dist",
        ],
        stdout=subprocess.PIPE,
    )
    assert process.stdout is not None
    with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
        archive.extractall(destination, filter="data")
    if process.wait() != 0:
        raise RuntimeError("复制管理端构建产物失败")


def wait_for_api(compose: list[str], timeout_seconds: int = 60) -> None:
    command = [
        *compose,
        "exec",
        "-T",
        "server",
        "python",
        "-c",
        (
            "import urllib.request; "
            "urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
        ),
    ]
    append_log("\n$ wait for server health\n")
    deadline = time.monotonic() + timeout_seconds
    last_output = ""
    while time.monotonic() < deadline:
        result = subprocess.run(
            command,
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            append_log("API 健康检查通过。\n")
            return
        last_output = (result.stdout + result.stderr).strip()
        time.sleep(3)
    if last_output:
        append_log(f"{last_output[-1000:]}\n")
    raise RuntimeError("API 在 60 秒内未通过健康检查")


def wait_for_admin(compose: list[str], timeout_seconds: int = 60) -> None:
    command = [
        *compose,
        "exec",
        "-T",
        "admin",
        "wget",
        "--spider",
        "http://127.0.0.1/",
    ]
    append_log("\n$ wait for admin health\n")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            command, cwd=REPOSITORY, capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            append_log("管理端健康检查通过。\n")
            return
        time.sleep(3)
    raise RuntimeError("管理端在 60 秒内未通过健康检查")


def deployed_targets() -> dict[str, dict[str, str | None]]:
    return {target: deployed_target(target) for target in ("server", "admin")}


def deployed_target(target: str) -> dict[str, str | None]:
    compose = [
        "docker",
        "compose",
        "--project-name",
        COMPOSE_PROJECT_NAME,
        "--env-file",
        ".env.production",
    ]
    container = subprocess.run(
        [*compose, "ps", "-q", target],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not container:
        return {"version": None, "deployedAt": None}
    image_id = subprocess.run(
        ["docker", "inspect", "--format", "{{.Image}}", container],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not image_id:
        return {"version": None, "deployedAt": None}
    labels_json = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", image_id],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    try:
        labels = json.loads(labels_json)
    except json.JSONDecodeError:
        labels = {}
    if not isinstance(labels, dict):
        labels = {}
    return {
        "version": labels.get("io.supertools.version"),
        "deployedAt": labels.get("io.supertools.deployed-at"),
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self) -> bool:
        return bool(TOKEN) and self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        elif not self.authorized():
            self.send_json(401, {"detail": "unauthorized"})
        elif self.path == "/status":
            payload = state.copy()
            payload["targets"] = deployed_targets()
            self.send_json(200, payload)
        else:
            self.send_json(404, {"detail": "not found"})

    def do_POST(self) -> None:
        if not self.authorized():
            self.send_json(401, {"detail": "unauthorized"})
            return
        target = {"/deploy/server": "server", "/deploy/admin": "admin"}.get(self.path)
        if target is None:
            self.send_json(404, {"detail": "not found"})
            return
        if not lock.acquire(blocking=False):
            self.send_json(409, {"detail": "deployment already running"})
            return
        state.update(
            status="running", target=target, startedAt=timestamp(), finishedAt=None, log=""
        )
        threading.Thread(target=run_deployment, args=(target,), daemon=True).start()
        self.send_json(202, state.copy())

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DEPLOY_SERVICE_TOKEN is required")
    if not (REPOSITORY / "docker-compose.yml").is_file():
        raise RuntimeError(f"docker-compose.yml not found in {REPOSITORY}")
    ThreadingHTTPServer(("0.0.0.0", 9010), Handler).serve_forever()
