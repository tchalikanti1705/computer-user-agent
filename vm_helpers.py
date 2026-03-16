import base64
import shlex
import subprocess


CONTAINER_NAME = "cua-image"
DISPLAY = ":99"


def docker_exec(cmd: str, container_name: str = CONTAINER_NAME, decode: bool = True):
    safe_cmd = cmd.replace('"', '\\"')
    full_cmd = f'docker exec {container_name} sh -lc "{safe_cmd}"'
    output = subprocess.check_output(full_cmd, shell=True)
    if decode:
        return output.decode("utf-8", errors="ignore")
    return output


def docker_exec_with_display(cmd: str, container_name: str = CONTAINER_NAME, decode: bool = True):
    wrapped = f"export DISPLAY={DISPLAY} && {cmd}"
    return docker_exec(wrapped, container_name=container_name, decode=decode)


def capture_screenshot(container_name: str = CONTAINER_NAME) -> bytes:
    docker_exec_with_display("import -window root /tmp/screen.png", container_name=container_name)
    return docker_exec("cat /tmp/screen.png", container_name=container_name, decode=False)


def capture_screenshot_base64(container_name: str = CONTAINER_NAME) -> str:
    png_bytes = capture_screenshot(container_name=container_name)
    return base64.b64encode(png_bytes).decode("utf-8")


def mouse_move(x: int, y: int, container_name: str = CONTAINER_NAME):
    docker_exec_with_display(f"xdotool mousemove {x} {y}", container_name=container_name)


def click(x: int, y: int, button: int = 1, container_name: str = CONTAINER_NAME):
    docker_exec_with_display(
        f"xdotool mousemove {x} {y} click {button}",
        container_name=container_name,
    )


def double_click(x: int, y: int, button: int = 1, container_name: str = CONTAINER_NAME):
    docker_exec_with_display(
        f"xdotool mousemove {x} {y} click --repeat 2 {button}",
        container_name=container_name,
    )


def type_text(text: str, container_name: str = CONTAINER_NAME):
    safe_text = shlex.quote(text)
    docker_exec_with_display(f"xdotool type --delay 50 {safe_text}", container_name=container_name)


def keypress(key: str, container_name: str = CONTAINER_NAME):
    docker_exec_with_display(f"xdotool key {shlex.quote(key)}", container_name=container_name)


def scroll_down(amount: int = 3, container_name: str = CONTAINER_NAME):
    for _ in range(amount):
        docker_exec_with_display("xdotool click 5", container_name=container_name)


def scroll_up(amount: int = 3, container_name: str = CONTAINER_NAME):
    for _ in range(amount):
        docker_exec_with_display("xdotool click 4", container_name=container_name)