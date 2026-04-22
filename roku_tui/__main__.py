import argparse
import asyncio
import sys

from .app import RokuTuiApp
from .service import RokuService


async def run_headless(command: str, ip: str | None = None, mock: bool = False) -> None:
    """Run a command sequence without a UI and then exit."""
    service = RokuService(mock=mock)
    try:
        if not mock:
            target_ip = ip or await service.discover()
            if not target_ip:
                print("Error: Could not find a Roku device on the network.")
                sys.exit(1)
            await service.connect(target_ip)
            
        await service.dispatch(command)
    finally:
        await service.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="roku-tui",
        description="Roku remote control as a terminal console",
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
    parser.add_argument(
        "-c", "--command",
        help="Execute commands (semicolon-separated) and exit (for automation)",
    )
    
    args = parser.parse_args()
    
    if args.command:
        try:
            asyncio.run(run_headless(args.command, ip=args.ip, mock=args.mock))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        app = RokuTuiApp(mock=args.mock, initial_ip=args.ip)
        app.run()


if __name__ == "__main__":
    main()
