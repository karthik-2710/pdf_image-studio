import sys
import os

# Ensure the root project directory is in the python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.app import App


def main():
    """Start the Image & PDF Converter Studio GUI application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
