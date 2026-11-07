"""
GemRadar Rug Checker - MCP server
=================================
Gives any MCP-capable agent (Claude Desktop, Claude Code, Cursor, ElizaOS MCP
plugin, ...) one tool: check_solana_token(mint).

Each call pays $0.01 USDC on Solana to the GemRadar Rug Checker API via x402.
Payment comes from YOUR wallet (SOLANA_PRIVATE_KEY). Use a small dedicated
wallet holding only a little USDC - never your main wallet.

Env:
  SOLANA_PRIVATE_KEY   base58 secret key, or JSON byte array (Solana CLI format)
  RUGCHECK_API         optional, default https://rugcheck.187-124-220-201.sslip.io
  RUGCHECK_MAX_USDC    optional spend cap per call, default 0.01
"""

import json
import os

from mcp.server.fastmcp import FastMCP
from solders.keypair import Keypair
from x402 import x402Client
from x402.client_base import max_amount  # spend cap: refuse any offer above RUGCHECK_MAX_USDC
from x402.http.clients import x402HttpxClient
from x402.mechanisms.svm.exact.register import register_exact_svm_client
from x402.mechanisms.svm.signers import KeypairSigner

API = os.getenv("RUGCHECK_API", "https://rugcheck.187-124-220-201.sslip.io").rstrip("/")
MAX_UNITS = int(round(float(os.getenv("RUGCHECK_MAX_USDC", "0.01")) * 1_000_000))  # USDC has 6 decimals

mcp = FastMCP("gemradar-rugcheck")


def _keypair() -> Keypair:
    key = os.environ.get("SOLANA_PRIVATE_KEY", "").strip()
    if not key:
        raise RuntimeError("Set SOLANA_PRIVATE_KEY to a small wallet holding a little USDC on Solana")
    if key.startswith("["):
        return Keypair.from_bytes(bytes(json.loads(key)))
    return Keypair.from_base58_string(key)


@mcp.tool()
async def check_solana_token(mint: str) -> dict:
    """Rug-risk check for a Solana token. Costs $0.01 USDC per call (paid automatically via x402).

    Returns verdict TRAP / NOT FLAGGED / UNKNOWN with plain-language reasons
    (dev team, sniper, bundler and insider holdings, insider early buyers) and
    warnings (cannot sell / honeypot, mint or freeze authority, thin liquidity).
    Backtest: tokens flagged TRAP lost >=50% within 6h 78% of the time vs 37% unflagged.
    Not financial advice.

    Args:
        mint: the token's Solana mint address
    """
    client = register_exact_svm_client(x402Client(), KeypairSigner(_keypair()), policies=[max_amount(MAX_UNITS)])
    async with x402HttpxClient(client, timeout=90) as http:
        r = await http.get(f"{API}/v1/check", params={"mint": mint})
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}", "detail": r.text[:500]}
    return r.json()


if __name__ == "__main__":
    mcp.run()
