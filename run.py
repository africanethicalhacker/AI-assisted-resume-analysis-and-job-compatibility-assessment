"""Development entry point: python run.py"""
import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    # debug is off by default; never run the debugger on a shared network.
    app.run(host="127.0.0.1", port=5000, debug=False)
