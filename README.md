# GemRadar Rug Checker

A rug-risk check for Solana tokens, built for AI agents and trading bots.
You pay **$0.01 USDC per check** over [x402](https://x402.org). There are no accounts, no API keys and no subscriptions.

```
GET https://rugcheck.187-124-220-201.sslip.io/v1/check?mint=<token mint>
```

Each check returns a **`TRAP`**, **`NOT FLAGGED`** or **`UNKNOWN`** verdict, with plain-language reasons and warnings:

- **Holder risk:** what share the dev team, snipers, bundlers and insiders hold
- **Insider early buyers:** whether insiders were among the first buyers (new launches only)
- **Sell test:** whether the token can actually be sold (honeypot detection), and the round-trip loss
- **Authorities:** whether mint or freeze authority is still active
- **Liquidity:** whether the pool is too thin to trade

## Evidence

The checker was backtested on 4,018 tradeable Solana tokens (Oct 17-28 2026):

- Tokens flagged **TRAP** lost at least 50% within 6 hours **78%** of the time, and 59% lost at least 90%.
- Unflagged tokens lost at least 50% **37%** of the time.
- The checker caught 67% of the tokens that crashed, and its accuracy held across both halves of the period.

This filters risk. It doesn't guarantee anything and isn't financial advice.

## Option 1: Use it from any AI agent (MCP)

`mcp_server.py` gives any MCP-capable agent, such as Claude Desktop, Claude Code, Cursor or the ElizaOS MCP plugin, one tool: `check_solana_token(mint)`. The tool pays automatically.

```bash
git clone https://github.com/hendfarouk1985-dot/gemradar-rugcheck
cd gemradar-rugcheck
pip install -r requirements.txt
```

Example MCP config (Claude Desktop `claude_desktop_config.json`, or `.mcp.json`):

```json
{
  "mcpServers": {
    "gemradar-rugcheck": {
      "command": "python",
      "args": ["/path/to/gemradar-rugcheck/mcp_server.py"],
      "env": { "SOLANA_PRIVATE_KEY": "<base58 key of a SMALL wallet holding a little USDC>" }
    }
  }
}
```

> **Use a dedicated wallet holding a few cents of USDC on Solana. Never use your main wallet.**
> The x402 facilitator pays the network fee, so the wallet needs only USDC, not SOL.
> Each call is capped at `RUGCHECK_MAX_USDC`, which defaults to `0.01`. The client refuses any higher price.

## Option 2: Call it from your own code (Python)

```python
import asyncio
from solders.keypair import Keypair
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.svm.exact.register import register_exact_svm_client
from x402.mechanisms.svm.signers import KeypairSigner

async def main():
    payer = Keypair.from_base58_string("<small wallet key>")
    client = register_exact_svm_client(x402Client(), KeypairSigner(payer))
    async with x402HttpxClient(client, timeout=90) as http:
        r = await http.get("https://rugcheck.187-124-220-201.sslip.io/v1/check",
                           params={"mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"})
        print(r.json())

asyncio.run(main())
```

Clients in other languages work too. Any x402 client (TypeScript, Go, and others; see [x402.org](https://x402.org)) can pay this endpoint, because the payment terms come back in the HTTP 402 response.

## Example response

```json
{
  "mint": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
  "symbol": "$WIF",
  "verdict": "NOT FLAGGED",
  "reasons": [],
  "warnings": [],
  "data": {
    "dev_team_pct": 0.0, "sniper_pct": 0.0, "bundler_pct": 0.1, "insider_pct": 0.0,
    "early_buyer_insider_pct": 0.0, "liquidity_usd": 1500000, "holders": 230000,
    "sell_test": {"tested": true, "can_sell": true, "round_trip_loss_pct": 0.2},
    "pool_age_days": 903.0
  }
}
```

The numbers above are illustrative.

## Free endpoints

- `GET /` gives service info and the price.
- `GET /health` returns the service status.

It is also listed on [x402scan](https://www.x402scan.com).

## License

MIT
