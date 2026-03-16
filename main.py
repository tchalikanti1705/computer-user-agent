import base64
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from vm_helpers import (
    capture_screenshot,
    click,
    double_click,
    keypress,
    mouse_move,
    scroll_down,
    scroll_up,
    type_text,
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def aget(action, key, default=None):
    if isinstance(action, dict):
        return action.get(key, default)
    return getattr(action, key, default)


def action_to_log(action) -> str:
    t = aget(action, "type")
    if t in ("click", "double_click", "move"):
        return f"{t}(x={aget(action, 'x')}, y={aget(action, 'y')})"
    if t == "scroll":
        return (
            f"scroll(x={aget(action, 'x')}, y={aget(action, 'y')}, "
            f"scrollX={aget(action, 'scrollX', 0)}, scrollY={aget(action, 'scrollY', 0)})"
        )
    if t == "type":
        return f"type(text={aget(action, 'text', '')!r})"
    if t == "keypress":
        return f"keypress(keys={aget(action, 'keys', [])})"
    return str(t)


def map_key(key: str) -> str:
    mapping = {
        "ENTER": "Return",
        "RETURN": "Return",
        "SPACE": "space",
        "TAB": "Tab",
        "ESC": "Escape",
        "ESCAPE": "Escape",
        "BACKSPACE": "BackSpace",
        "DELETE": "Delete",
        "UP": "Up",
        "DOWN": "Down",
        "LEFT": "Left",
        "RIGHT": "Right",
        "HOME": "Home",
        "END": "End",
        "PAGEUP": "Page_Up",
        "PAGEDOWN": "Page_Down",
        "CTRL": "ctrl",
        "CONTROL": "ctrl",
        "ALT": "alt",
        "SHIFT": "shift",
        "CMD": "super",
        "SUPER": "super",
    }
    return mapping.get(str(key).upper(), str(key))


def handle_keypress(keys):
    if not keys:
        return

    mapped = [map_key(k) for k in keys]

    if len(mapped) == 1:
        keypress(mapped[0])
    else:
        combo = "+".join(mapped)
        keypress(combo)


def handle_computer_actions(actions):
    for action in actions:
        print("ACTION:", action_to_log(action))

        action_type = aget(action, "type")

        if action_type == "click":
            button_map = {"left": 1, "middle": 2, "right": 3}
            click(
                aget(action, "x"),
                aget(action, "y"),
                button=button_map.get(aget(action, "button", "left"), 1),
            )

        elif action_type == "double_click":
            button_map = {"left": 1, "middle": 2, "right": 3}
            double_click(
                aget(action, "x"),
                aget(action, "y"),
                button=button_map.get(aget(action, "button", "left"), 1),
            )

        elif action_type == "move":
            mouse_move(aget(action, "x"), aget(action, "y"))

        elif action_type == "scroll":
            mouse_move(aget(action, "x"), aget(action, "y"))
            sx = aget(action, "scrollX", 0)
            sy = aget(action, "scrollY", 0)

            if sy > 0:
                steps = max(1, abs(sy) // 200)
                scroll_down(steps)
            elif sy < 0:
                steps = max(1, abs(sy) // 200)
                scroll_up(steps)

            if sx != 0:
                print("NOTE: horizontal scroll requested but not implemented.")

        elif action_type == "keypress":
            handle_keypress(aget(action, "keys", []))

        elif action_type == "type":
            type_text(aget(action, "text", ""))

        elif action_type == "wait":
            time.sleep(2)

        elif action_type == "screenshot":
            pass

        else:
            raise ValueError(f"Unsupported action type: {action_type}")


def get_computer_call(response):
    for item in response.output:
        item_type = item["type"] if isinstance(item, dict) else getattr(item, "type", None)
        if item_type == "computer_call":
            return item
    return None


def get_output_items(response):
    if hasattr(response, "output"):
        return response.output
    if isinstance(response, dict):
        return response.get("output", [])
    return []


def print_model_messages(response):
    for item in get_output_items(response):
        item_type = item["type"] if isinstance(item, dict) else getattr(item, "type", None)
        if item_type == "message":
            content = item["content"] if isinstance(item, dict) else getattr(item, "content", [])
            for c in content:
                c_type = c["type"] if isinstance(c, dict) else getattr(c, "type", None)
                if c_type in ("output_text", "text"):
                    text = c["text"] if isinstance(c, dict) else getattr(c, "text", "")
                    print("MODEL:", text)


def get_response_id(response):
    if isinstance(response, dict):
        return response.get("id")
    return getattr(response, "id", None)


def get_call_id(computer_call):
    if isinstance(computer_call, dict):
        return computer_call.get("call_id")
    return getattr(computer_call, "call_id", None)


def get_actions(computer_call):
    if isinstance(computer_call, dict):
        return computer_call.get("actions", [])
    return getattr(computer_call, "actions", [])


def computer_use_loop(user_message: str):
    response = client.responses.create(
        model="gpt-5.4",
        tools=[{"type": "computer"}],
        input=user_message,
    )
    print(f"response_id={get_response_id(response)}")

    while True:
        print_model_messages(response)
        computer_call = get_computer_call(response)

        if computer_call is None:
            print("\nFINAL: no more computer_call items.")
            return response

        actions = get_actions(computer_call)
        handle_computer_actions(actions)

        screenshot_bytes = capture_screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        response = client.responses.create(
            model="gpt-5.4",
            tools=[{"type": "computer"}],
            previous_response_id=get_response_id(response),
            input=[
                {
                    "type": "computer_call_output",
                    "call_id": get_call_id(computer_call),
                    "output": {
                        "type": "computer_screenshot",
                        "image_url": f"data:image/png;base64,{screenshot_base64}",
                        "detail": "original",
                    },
                }
            ],
        )
        print(f"response_id={get_response_id(response)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True, help="Task instruction for the computer-use agent")
    args = parser.parse_args()

    computer_use_loop(args.message)