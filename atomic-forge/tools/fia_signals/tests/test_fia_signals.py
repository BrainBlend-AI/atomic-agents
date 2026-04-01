import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.fia_signals import (  # noqa: E402
    FIASignalsTool,
    FIASignalsToolConfig,
    FIASignalsToolInputSchema,
)


# --- Fixtures ---

@pytest.fixture
def tool():
    return FIASignalsTool(config=FIASignalsToolConfig())


# --- Input Schema Tests ---

def test_input_schema_tool_field():
    schema = FIASignalsToolInputSchema.model_json_schema()
    assert "tool" in schema["properties"]
    props = schema["properties"]["tool"]
    enum_vals = props["enum"]
    assert "market_regime" in enum_vals
    assert "crypto_signals" in enum_vals
    assert "defi_yields" in enum_vals
    assert "gas_prices" in enum_vals
    assert "solana_trending" in enum_vals
    assert "wallet_risk" in enum_vals


def test_input_schema_optional_fields():
    schema = FIASignalsToolInputSchema.model_json_schema()
    assert schema["properties"]["symbol"].get("anyOf") is not None
    assert schema["properties"]["address"].get("anyOf") is not None


# --- Tool instantiation ---

def test_tool_instantiation():
    tool = FIASignalsTool()
    assert tool.api_key is None


def test_tool_with_config():
    tool = FIASignalsTool(config=FIASignalsToolConfig(api_key="test-key"))
    assert tool.api_key == "test-key"


# --- Mocked API tests ---

@pytest.mark.parametrize("tool_name,endpoint", [
    ("market_regime", "/v1/intelligence/regime/free"),
    ("defi_yields", "/v1/yield/rates"),
    ("gas_prices", "/v1/gas/prices"),
    ("solana_trending", "/v1/solana/trending"),
])
def test_tool_free_endpoints(tool, tool_name, endpoint):
    mock_response = {"test": "data", "regime": "TRENDING_UP"}

    with patch("tool.fia_signals.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            ok=True, status_code=200,
            json=MagicMock(return_value=mock_response)
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = tool.run(FIASignalsToolInputSchema(tool=tool_name))

        assert result.tool == tool_name
        assert result.data == mock_response
        mock_get.assert_called_once()


def test_crypto_signals_default_symbol(tool):
    mock_response = {"signal": "BUY", "rsi": 45.2}

    with patch("tool.fia_signals.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            ok=True, status_code=200,
            json=MagicMock(return_value=mock_response)
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = tool.run(FIASignalsToolInputSchema(tool="crypto_signals"))

        assert result.tool == "crypto_signals"
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "BTC" in call_url  # default symbol


def test_crypto_signals_custom_symbol(tool):
    mock_response = {"signal": "SELL", "rsi": 68.1}

    with patch("tool.fia_signals.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            ok=True, status_code=200,
            json=MagicMock(return_value=mock_response)
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = tool.run(FIASignalsToolInputSchema(tool="crypto_signals", symbol="DOGE"))

        assert result.tool == "crypto_signals"
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "DOGE" in call_url


def test_wallet_risk_no_address_raises(tool):
    with pytest.raises(ValueError, match="address is required"):
        tool.run(FIASignalsToolInputSchema(tool="wallet_risk"))


def test_wallet_risk_returns_x402_info(tool):
    result = tool.run(FIASignalsToolInputSchema(
        tool="wallet_risk",
        address="0x1234567890abcdef1234567890abcdef12345678"
    ))

    assert result.tool == "wallet_risk"
    assert "x402" in result.data["gateway"]
    assert result.data["price"] == "$0.02 USDC"


# --- Error handling ---

def test_api_error_raises(tool):
    with patch("tool.fia_signals.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            ok=False, status_code=500,
            raise_for_status=MagicMock(
                side_effect=Exception("500 Server Error")
            )
        )
        with pytest.raises(Exception):
            tool.run(FIASignalsToolInputSchema(tool="market_regime"))
