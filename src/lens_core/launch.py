"""`lens-core` launcher (stub).

Stands up a Lens lab: applies the shared schema standard and reports which modules
are composed. Stdlib-only so `lens-core --help` works the moment pip install
completes. The database is INJECTED via LENS_DB_URL — never hardcoded.

This is a scaffold: it validates inputs and prints the plan. Schema application +
module wiring land in follow-up commits.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

MODULES = ["lens-ingest", "lens-review", "lens-serve", "lens-observe"]
SCHEMA = Path(__file__).resolve().parents[2] / "docs" / "schema" / "spine.sql"


def _cmd_new(args: argparse.Namespace) -> int:
    db = args.db_url or os.environ.get("LENS_DB_URL")
    if not db:
        print("error: no database. Set LENS_DB_URL or pass --db-url "
              "(the connection is injected, never hardcoded).", file=sys.stderr)
        return 1
    print(f"==> Launching a Lens lab")
    print(f"    database:  {db.split('@')[-1] if '@' in db else '(set)'}")
    print(f"    standard:  {SCHEMA}")
    print(f"    modules:   {', '.join(args.modules or MODULES)}")
    print()
    print("STUB: schema application + module wiring not implemented yet.")
    print("      Next commit applies docs/schema/spine.sql and registers modules.")
    return 0


def _cmd_version(_args: argparse.Namespace) -> int:
    from lens_core import __version__
    print(f"lens-core {__version__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lens-core", description="The Lens — launch a lab (systems observatory).")
    subs = p.add_subparsers(dest="command", metavar="<command>")

    new = subs.add_parser("new", help="Stand up a new lab against an injected database.")
    new.add_argument("--db-url", default=None, help="Database URL (default: LENS_DB_URL env).")
    new.add_argument("--modules", nargs="*", default=None,
                     help=f"Modules to compose (default: {', '.join(MODULES)}).")
    new.set_defaults(func=_cmd_new)

    subs.add_parser("version", help="Print version.").set_defaults(func=_cmd_version)

    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        p.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
