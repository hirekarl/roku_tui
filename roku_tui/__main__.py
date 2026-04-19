import argparse

from .app import RokuTuiApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="roku-tui",
        description="Roku remote control as a terminal REPL",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run without a real Roku device (simulates HTTP responses)",
    )
    parser.add_argument(
        "--ip",
        default=None,
        metavar="IP",
        help="Roku IP address (skips SSDP discovery)",
    )
    args = parser.parse_args()
    app = RokuTuiApp(mock=args.mock, initial_ip=args.ip)
    app.run()


if __name__ == "__main__":
    main()
