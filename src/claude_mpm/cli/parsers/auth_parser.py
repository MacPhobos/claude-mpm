"""
Auth command parser for claude-mpm CLI.

WHY: Provides the 'auth' top-level command with subcommands for managing
gworkspace-mcp OAuth tokens stored in .gworkspace-mcp/tokens.json.
Unlike 'claude-mpm oauth refresh', this command bypasses the encrypted
token store and refreshes tokens directly via the Google OAuth2 endpoint.
"""

import argparse

from .base_parser import add_common_arguments


def add_auth_subparser(subparsers) -> argparse.ArgumentParser:
    """Add the auth subparser with refresh and status subcommands.

    Args:
        subparsers: The subparsers object from the main parser

    Returns:
        The configured auth subparser
    """
    auth_parser = subparsers.add_parser(
        "auth",
        help="Manage authentication tokens for MCP services",
        description="""
Manage authentication tokens stored by MCP services.

Available commands:
  refresh   Refresh tokens without a browser (uses stored refresh_token)
  status    Show token expiry status for all services

Token file: .gworkspace-mcp/tokens.json (relative to project root)
Credentials: GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET
             (read from .env.local first, then environment variables)

Examples:
  claude-mpm auth refresh
  claude-mpm auth refresh --service gworkspace-mcp
  claude-mpm auth refresh --all
  claude-mpm auth status
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_common_arguments(auth_parser)

    auth_subparsers = auth_parser.add_subparsers(
        dest="auth_command", help="Auth commands", metavar="SUBCOMMAND"
    )

    # refresh subcommand
    refresh_parser = auth_subparsers.add_parser(
        "refresh",
        help="Refresh tokens using stored refresh_token (no browser required)",
        description=(
            "Refresh the access token for an MCP service by posting the stored "
            "refresh_token to the Google OAuth2 token endpoint. "
            "Credentials are loaded from .env.local, then environment variables."
        ),
    )
    add_common_arguments(refresh_parser)
    refresh_parser.add_argument(
        "--service",
        default="gworkspace-mcp",
        help="Service name to refresh (default: gworkspace-mcp)",
    )
    refresh_parser.add_argument(
        "--all",
        action="store_true",
        dest="all",
        help="Refresh tokens for all services found in the token file",
    )

    # status subcommand
    status_parser = auth_subparsers.add_parser(
        "status",
        help="Show token expiry status for all services",
        description="Display token expiry information from .gworkspace-mcp/tokens.json.",
    )
    add_common_arguments(status_parser)

    return auth_parser
