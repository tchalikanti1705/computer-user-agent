from vm_helpers import click, keypress, type_text, capture_screenshot


def main():
    keypress("ctrl+l")
    type_text("https://www.example.com")
    keypress("Return")

    png = capture_screenshot()
    print(f"Captured screenshot bytes: {len(png)}")


if __name__ == "__main__":
    main()