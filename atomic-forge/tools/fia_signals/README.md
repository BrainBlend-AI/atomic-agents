# Fía Signals Tool

**Professional-grade crypto market intelligence for Atomic Agents.**

Provides 6 tools backed by real-time data from Binance, DeFiLlama, Etherscan, and more:

| Tool | Description | Free? |
|------|-------------|-------|
| `market_regime` | Detect trending/ranging/volatile/breakout market regime | ✅ Free |
| `crypto_signals` | BUY/SELL/HOLD with RSI, MACD, ADX for any crypto | ✅ Free |
| `defi_yields` | Best yields across Aave, Compound, Curve, Lido | ✅ Free |
| `gas_prices` | Real-time gas across Ethereum, Polygon, BSC, Arbitrum, Base | ✅ Free |
| `solana_trending` | Trending Solana tokens with volume and risk scores | ✅ Free |
| `wallet_risk` | Wallet risk score + entity classification | x402 $0.02 |

## Installation

```bash
pip install fia-signals
```

No API key required for free tier. Premium `wallet_risk` tool uses x402 micropayments (Solana USDC).

## Usage

```python
from fia_signals_tool import FIASignalsTool, FIASignalsToolInputSchema

tool = FIASignalsTool()

# Market regime
result = tool.run(FIASignalsToolInputSchema(tool="market_regime"))
print(result.data)

# Crypto signals
result = tool.run(FIASignalsToolInputSchema(tool="crypto_signals", symbol="ETH"))
print(result.data)

# DeFi yields
result = tool.run(FIASignalsToolInputSchema(tool="defi_yields"))
print(result.data)
```

## Atomic Agents

Add to your `atomic-agents` project via the workspace `pyproject.toml`:

```toml
[tool.uv.workspace]
members = ["atomic-forge/tools/fia_signals"]
```

## License

MIT
