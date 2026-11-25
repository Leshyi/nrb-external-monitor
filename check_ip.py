
import socket
import subprocess
import sys
from datetime import datetime, timezone

TARGET = "103.231.179.50"

def check_ip():
    try:
        result = subprocess.run(
            ["ping", "-c", "3", "-W", "5", TARGET],
            capture_output=True,
            text=True,
            timeout=20
        )

        if result.returncode == 0:
            print(f"UP: {TARGET}")
            print(result.stdout)
            return True

        print(f"DOWN: {TARGET}")
        print(result.stdout)
        return False

    except Exception as error:
        print(f"ERROR: {error}")
        return False

if __name__ == "__main__":
    print("NRB External IP Monitor")
    print(datetime.now(timezone.utc).isoformat())
    sys.exit(0 if check_ip() else 1)
