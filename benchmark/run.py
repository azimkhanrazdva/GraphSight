from __future__ import annotations

import json


def main() -> None:
    print(json.dumps({"status": "pending", "message": "No benchmark dataset has been executed."}, indent=2))


if __name__ == "__main__":
    main()

