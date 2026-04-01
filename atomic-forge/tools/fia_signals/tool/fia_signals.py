import os
from typing import Literal, Optional

import requests
from pydantic import Field

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig


BASE_URL = "https://fiasignals.com"


################
# INPUT SCHEMA #
################
class FIASignalsToolInputSchema(BaseIOSchema):
    """
    Schema for input to the Fía Signals crypto intelligence tool.
    Select one tool at a time.
    """

    tool: Literal[
        "market_regime",
        "crypto_signals",
        "defi_yields",
        "gas_prices",
        "solana_trending",
        "wallet_risk",
    ] = Field(..., description="The Fía Signals tool to call.")
    symbol: Optional[str] = Field(
        None, description="Crypto symbol (e.g. BTC, ETH) for crypto_signals tool."
    )
    address: Optional[str] = Field(
        None, description="Wallet address for wallet_risk tool."
    )


####################
# OUTPUT SCHEMA(S) #
####################
class FIAMarketRegimeOutputSchema(BaseIOSchema):
    """Output schema for market regime detection."""

    regime: str = Field(..., description="Market regime: TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE, BREAKOUT")
    confidence: float = Field(..., description="Confidence score of the regime classification (0-1)")
    indicators: dict = Field(..., description="Supporting indicators used for classification")


class FIACryptoSignalsOutputSchema(BaseIOSchema):
    """Output schema for crypto trading signals."""

    signal: str = Field(..., description="Trading signal: BUY, SELL, or HOLD")
    symbol: str = Field(..., description="Crypto symbol")
    rsi: float = Field(..., description="Relative Strength Index (0-100)")
    macd: dict = Field(..., description="MACD indicator values")
    adx: float = Field(..., description="Average Directional Index (0-100)")
    entry: Optional[dict] = Field(None, description="Suggested entry zone")
    target: Optional[dict] = Field(None, description="Suggested target zone")
    stop: Optional[dict] = Field(None, description="Suggested stop loss")


class FIDefiYieldsOutputSchema(BaseIOSchema):
    """Output schema for DeFi yields."""

    yields: list = Field(..., description="List of DeFi yield opportunities")
    protocol: str = Field(..., description="Protocol name (Aave, Compound, Curve, Lido)")
    asset: str = Field(..., description="Underlying asset")
    apy: float = Field(..., description="Annual Percentage Yield")


class FIAGasPricesOutputSchema(BaseIOSchema):
    """Output schema for gas prices."""

    network: str = Field(..., description="Network name (Ethereum, Polygon, BSC, Arbitrum, Base)")
    gas_price_gwei: float = Field(..., description="Current gas price in Gwei")


class FIASolanaTrendingOutputSchema(BaseIOSchema):
    """Output schema for trending Solana tokens."""

    tokens: list = Field(..., description="List of trending Solana tokens")
    symbol: str = Field(..., description="Token symbol")
    volume_24h: float = Field(..., description="24-hour trading volume")
    risk_score: float = Field(..., description="Risk score (0-1)")


class FIAWalletRiskOutputSchema(BaseIOSchema):
    """Output schema for wallet risk scoring."""

    address: str = Field(..., description="Wallet address")
    risk_score: float = Field(..., description="Wallet risk score (0-1)")
    entity: Optional[str] = Field(None, description="Entity classification if known")
    tags: list = Field(..., description="Behavioral tags")


class FIASignalsToolOutputSchema(BaseIOSchema):
    """Output schema for the Fía Signals tool — wraps all tool responses."""

    tool: str = Field(..., description="Tool that was called")
    data: dict = Field(..., description="Raw response data from Fía Signals API")


##############
# TOOL CONFIG #
##############
class FIASignalsToolConfig(BaseToolConfig):
    """Configuration for the Fía Signals tool."""

    api_key: Optional[str] = None  # Free tier requires no API key; x402 premium uses Solana USDC


##############
# TOOL LOGIC #
##############
class FIASignalsTool(BaseTool[FIASignalsToolInputSchema, FIASignalsToolOutputSchema]):
    """
    Tool for accessing Fía Signals crypto market intelligence.

    Provides market regime detection, trading signals (RSI/MACD/ADX),
    DeFi yields, gas prices, Solana trending tokens, and wallet risk scoring.

    Attributes:
        input_schema (FIASignalsToolInputSchema): The schema for the input data.
        output_schema (FIASignalsToolOutputSchema): The schema for the output data.
    """

    def __init__(self, config: FIASignalsToolConfig = FIASignalsToolConfig()):
        """
        Initializes the FIASignalsTool.

        Args:
            config (FIASignalsToolConfig): Configuration for the tool.
        """
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("FIA_API_KEY")

    def _call_tool(self, params: FIASignalsToolInputSchema) -> dict:
        """Dispatch to the appropriate Fía Signals API endpoint."""
        tool = params.tool

        if tool == "market_regime":
            r = requests.get(f"{BASE_URL}/v1/intelligence/regime/free", timeout=10)
            r.raise_for_status()
            return {"tool": "market_regime", "data": r.json()}

        elif tool == "crypto_signals":
            symbol = params.symbol or "BTC"
            r = requests.get(f"{BASE_URL}/v1/dd/quick/{symbol}", timeout=10)
            r.raise_for_status()
            return {"tool": "crypto_signals", "data": r.json()}

        elif tool == "defi_yields":
            r = requests.get(f"{BASE_URL}/v1/yield/rates", timeout=10)
            r.raise_for_status()
            return {"tool": "defi_yields", "data": r.json()}

        elif tool == "gas_prices":
            r = requests.get(f"{BASE_URL}/v1/gas/prices", timeout=10)
            r.raise_for_status()
            return {"tool": "gas_prices", "data": r.json()}

        elif tool == "solana_trending":
            r = requests.get(f"{BASE_URL}/v1/solana/trending", timeout=10)
            r.raise_for_status()
            return {"tool": "solana_trending", "data": r.json()}

        elif tool == "wallet_risk":
            if not params.address:
                raise ValueError("address is required for wallet_risk tool")
            return {
                "tool": "wallet_risk",
                "data": {
                    "info": "Premium endpoint — requires x402 micropayment",
                    "gateway": "https://x402.fiasignals.com",
                    "endpoint": f"/v1/wallet/risk/{params.address}",
                    "price": "$0.02 USDC",
                    "discovery": "https://x402.fiasignals.com/.well-known/x402.json",
                },
            }

        raise ValueError(f"Unknown tool: {tool}")

    async def run_async(
        self, params: FIASignalsToolInputSchema
    ) -> FIASignalsToolOutputSchema:
        """
        Runs the Fía Signals tool asynchronously.

        Args:
            params (FIASignalsToolInputSchema): The input parameters.

        Returns:
            FIASignalsToolOutputSchema: The output from the selected tool.
        """
        import asyncio

        result = await asyncio.to_thread(self._call_tool, params)
        return FIASignalsToolOutputSchema(**result)

    def run(self, params: FIASignalsToolInputSchema) -> FIASignalsToolOutputSchema:
        """
        Runs the Fía Signals tool synchronously.

        Args:
            params (FIASignalsToolInputSchema): The input parameters.

        Returns:
            FIASignalsToolOutputSchema: The output from the selected tool.
        """
        result = self._call_tool(params)
        return FIASignalsToolOutputSchema(**result)


####
# Main entry point for testing
if __name__ == "__main__":
    from rich.console import Console

    rich_console = Console()

    tool = FIASignalsTool()

    # Test: market regime
    rich_console.print("[bold]Testing market_regime...[/bold]")
    output = tool.run(FIASignalsToolInputSchema(tool="market_regime"))
    rich_console.print(output)

    # Test: crypto signals
    rich_console.print("\n[bold]Testing crypto_signals (BTC)...[/bold]")
    output = tool.run(FIASignalsToolInputSchema(tool="crypto_signals", symbol="BTC"))
    rich_console.print(output)
