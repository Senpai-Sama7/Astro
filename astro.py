#!/usr/bin/env python3
"""
ASTRO - Launch the Terminal UI

Usage:
    python -m astro          # Launch TUI
    python -m astro --cli    # Launch CLI mode
    python -m astro --help   # Show help
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="ASTRO - AI-Powered Terminal Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    astro              Launch the beautiful Terminal UI
    astro --cli        Launch classic CLI mode
    astro --web        Open web interface in browser
        """
    )
    parser.add_argument("--cli", action="store_true", help="Use classic CLI mode")
    parser.add_argument("--web", action="store_true", help="Open web interface")
    parser.add_argument("--api-url", default="http://localhost:5000", help="API server URL")
    
    args = parser.parse_args()
    
    if args.web:
        import webbrowser
        webbrowser.open(args.api_url)
        print(f"Opening {args.api_url} in your browser...")
        return
    
    if args.cli:
        from src.cli.agent import AstroCLI
        cli = AstroCLI(api_url=args.api_url)
        cli.run()
    else:
        try:
            from src.tui.app import main as tui_main
            tui_main()
        except ImportError as e:
            print(f"TUI dependencies not installed: {e}")
            print("Install with: pip install textual rich")
            print("\nFalling back to CLI mode...\n")
            from src.cli.agent import AstroCLI
            cli = AstroCLI(api_url=args.api_url)
            cli.run()


if __name__ == "__main__":
    main()
