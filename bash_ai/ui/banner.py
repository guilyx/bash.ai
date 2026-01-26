import sys
import time

FLOURISH_BANNER = """
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║  ███████╗██╗      ██████╗ ██╗   ██╗██████╗ ██╗███████╗██╗  ██╗         ║
║  ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██║██╔════╝██║  ██║         ║
║  █████╗  ██║     ██║   ██║██║   ██║██████╔╝██║███████╗███████║         ║
║  ██╔══╝  ██║     ██║   ██║██║   ██║██╔══██╗██║╚════██║██╔══██║         ║
║  ██║     ███████╗╚██████╔╝╚██████╔╝██║  ██║██║███████║██║  ██║         ║
║  ╚═╝     ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝         ║
║                                                                        ║
║                    AI-Powered Terminal Environment                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
"""

def animate_banner(speed=0.03):
    """Prints the banner with a vertical scanline effect."""
    cyan = "\033[36m"
    reset = "\033[0m"

    lines = FLOURISH_BANNER.strip().split("\n")

    for line in lines:
        # Print line with cyan color
        sys.stdout.write(cyan + line + reset + "\n")
        sys.stdout.flush()
        time.sleep(speed)
    print()

def print_banner():
    animate_banner()

if __name__ == "__main__":
    animate_banner()