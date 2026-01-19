#!/usr/bin/env python3
"""
Huckleberry CLI - Baby tracking from the command line

Usage:
    hb children                     List children
    hb sleep start                  Start sleep
    hb sleep stop                   Complete sleep
    hb sleep pause                  Pause sleep
    hb sleep resume                 Resume sleep
    hb sleep cancel                 Cancel sleep
    hb feed start [--side=left]     Start breastfeeding
    hb feed stop                    Complete feeding
    hb feed switch                  Switch sides
    hb feed bottle <amount> [--type=formula] [--units=ml]
    hb diaper <mode> [--color=X] [--consistency=X]
    hb growth [--weight=X] [--height=X] [--head=X]
    hb status                       Current active timers
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    from huckleberry_api import HuckleberryAPI
except ImportError:
    print("Error: huckleberry-api not installed")
    print("Run: pip install huckleberry-api")
    sys.exit(1)


CONFIG_PATH = Path.home() / ".config" / "huckleberry" / "config.json"


def load_config():
    """Load configuration from file."""
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config):
    """Save configuration to file."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    CONFIG_PATH.chmod(0o600)


def get_api():
    """Get authenticated API instance."""
    config = load_config()
    if not config:
        email = os.environ.get("HUCKLEBERRY_EMAIL")
        password = os.environ.get("HUCKLEBERRY_PASSWORD")
        timezone = os.environ.get("HUCKLEBERRY_TIMEZONE", "America/Los_Angeles")
        
        if not email or not password:
            print("Error: Not configured. Run 'hb login' first or set environment variables:")
            print("  HUCKLEBERRY_EMAIL")
            print("  HUCKLEBERRY_PASSWORD")
            print("  HUCKLEBERRY_TIMEZONE (optional)")
            sys.exit(1)
    else:
        email = config.get("email")
        password = config.get("password")
        timezone = config.get("timezone", "America/Los_Angeles")
    
    api = HuckleberryAPI(email=email, password=password, timezone=timezone)
    api.authenticate()
    return api


def get_child_uid(api, child_name=None):
    """Get child UID, optionally by name."""
    children = api.get_children()
    if not children:
        print("Error: No children found")
        sys.exit(1)
    
    if child_name:
        for child in children:
            if child.get("name", "").lower() == child_name.lower():
                return child["uid"]
        print(f"Error: Child '{child_name}' not found")
        sys.exit(1)
    
    return children[0]["uid"]


def cmd_login(args):
    """Configure credentials."""
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    timezone = input("Timezone (default: America/Los_Angeles): ").strip() or "America/Los_Angeles"
    
    print("Testing authentication...")
    try:
        api = HuckleberryAPI(email=email, password=password, timezone=timezone)
        api.authenticate()
        children = api.get_children()
        print(f"✓ Authenticated! Found {len(children)} child(ren)")
        for child in children:
            print(f"  - {child.get('name', 'Unknown')}")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)
    
    save_config({"email": email, "password": password, "timezone": timezone})
    print(f"✓ Config saved to {CONFIG_PATH}")


def cmd_children(args):
    """List children."""
    api = get_api()
    children = api.get_children()
    
    if args.json:
        print(json.dumps(children, indent=2, default=str))
        return
    
    for child in children:
        print(f"• {child.get('name', 'Unknown')} (uid: {child['uid']})")
        if "birthDate" in child:
            print(f"  Born: {child['birthDate']}")


def cmd_sleep(args):
    """Sleep tracking commands."""
    api = get_api()
    child_uid = get_child_uid(api, args.child)
    
    action = args.action
    
    if action == "start":
        api.start_sleep(child_uid)
        print("💤 Sleep started")
    elif action == "stop":
        api.complete_sleep(child_uid)
        print("💤 Sleep completed")
    elif action == "pause":
        api.pause_sleep(child_uid)
        print("💤 Sleep paused")
    elif action == "resume":
        api.resume_sleep(child_uid)
        print("💤 Sleep resumed")
    elif action == "cancel":
        api.cancel_sleep(child_uid)
        print("💤 Sleep cancelled")


def cmd_feed(args):
    """Feeding tracking commands."""
    api = get_api()
    child_uid = get_child_uid(api, args.child)
    
    action = args.action
    
    if action == "start":
        side = getattr(args, "side", "left") or "left"
        api.start_feeding(child_uid, side=side)
        print(f"🍼 Feeding started ({side} side)")
    elif action == "stop":
        api.complete_feeding(child_uid)
        print("🍼 Feeding completed")
    elif action == "switch":
        api.switch_feeding_side(child_uid)
        print("🍼 Switched sides")
    elif action == "bottle":
        amount = args.amount
        bottle_type = args.type or "Formula"
        units = args.units or "ml"
        api.log_bottle_feeding(child_uid, amount=float(amount), bottle_type=bottle_type, units=units)
        print(f"🍼 Bottle logged: {amount}{units} {bottle_type}")


def cmd_diaper(args):
    """Log diaper change."""
    api = get_api()
    child_uid = get_child_uid(api, args.child)
    
    kwargs = {"mode": args.mode}
    if args.color:
        kwargs["color"] = args.color
    if args.consistency:
        kwargs["consistency"] = args.consistency
    
    api.log_diaper(child_uid, **kwargs)
    
    emoji = "💩" if args.mode in ("poo", "both") else "💧" if args.mode == "pee" else "🧷"
    print(f"{emoji} Diaper logged: {args.mode}")


def cmd_growth(args):
    """Log growth measurements."""
    api = get_api()
    child_uid = get_child_uid(api, args.child)
    
    kwargs = {"units": args.units or "metric"}
    if args.weight:
        kwargs["weight"] = float(args.weight)
    if args.height:
        kwargs["height"] = float(args.height)
    if args.head:
        kwargs["head"] = float(args.head)
    
    if len(kwargs) == 1:
        print("Error: Provide at least one measurement")
        sys.exit(1)
    
    api.log_growth(child_uid, **kwargs)
    print("📏 Growth logged")


def cmd_status(args):
    """Show current status."""
    api = get_api()
    children = api.get_children()
    print("📊 Huckleberry Status")
    for child in children:
        print(f"\n👶 {child.get('name', 'Unknown')}")


def main():
    parser = argparse.ArgumentParser(prog="huckleberry", description="Huckleberry baby tracker CLI")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--child", "-c", help="Child name")
    
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("login", help="Configure credentials")
    subparsers.add_parser("children", help="List children")
    
    sleep_parser = subparsers.add_parser("sleep", help="Sleep tracking")
    sleep_parser.add_argument("action", choices=["start", "stop", "pause", "resume", "cancel"])
    
    feed_parser = subparsers.add_parser("feed", help="Feeding tracking")
    feed_parser.add_argument("action", choices=["start", "stop", "switch", "bottle"])
    feed_parser.add_argument("amount", nargs="?", type=float)
    feed_parser.add_argument("--side", "-s", choices=["left", "right"], default="left")
    feed_parser.add_argument("--type", "-t", choices=["Breast Milk", "Formula", "Mixed"], default="Formula")
    feed_parser.add_argument("--units", "-u", choices=["ml", "oz"], default="ml")
    
    diaper_parser = subparsers.add_parser("diaper", help="Log diaper change")
    diaper_parser.add_argument("mode", choices=["pee", "poo", "both", "dry"])
    diaper_parser.add_argument("--color", choices=["yellow", "green", "brown", "black", "red"])
    diaper_parser.add_argument("--consistency", choices=["runny", "soft", "solid", "hard"])
    
    growth_parser = subparsers.add_parser("growth", help="Log growth measurements")
    growth_parser.add_argument("--weight", "-w", type=float)
    growth_parser.add_argument("--height", type=float)
    growth_parser.add_argument("--head", type=float)
    growth_parser.add_argument("--units", choices=["metric", "imperial"], default="metric")
    
    subparsers.add_parser("status", help="Show current status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    commands = {
        "login": cmd_login,
        "children": cmd_children,
        "sleep": cmd_sleep,
        "feed": cmd_feed,
        "diaper": cmd_diaper,
        "growth": cmd_growth,
        "status": cmd_status,
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        try:
            cmd_func(args)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
