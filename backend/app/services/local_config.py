"""
Local config management mock for development
"""

import os
import json
from typing import Dict, List, Any
from pathlib import Path

def get_local_config_path():
    """Get path for local config storage"""
    return Path(__file__).parent.parent.parent / "local_config"

def load_local_config(config_type: str) -> Dict[str, Any]:
    """Load config from local file"""
    config_path = get_local_config_path() / f"{config_type}.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                symbols = json.load(f)
            return {
                "success": True,
                "symbols": symbols,
                "count": len(symbols),
                "source": "local"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading local config: {str(e)}"
            }
    else:
        # Return default symbols if no config exists
        default_symbols = get_default_symbols(config_type)
        return {
            "success": True,
            "symbols": default_symbols,
            "count": len(default_symbols),
            "source": "default"
        }

def save_local_config(config_type: str, symbols: List[str]) -> Dict[str, Any]:
    """Save config to local file"""
    config_path = get_local_config_path()
    config_path.mkdir(exist_ok=True)
    
    try:
        with open(config_path / f"{config_type}.json", 'w') as f:
            json.dump(symbols, f, indent=2)
        return {
            "success": True,
            "message": f"Saved {len(symbols)} symbols to local config"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error saving local config: {str(e)}"
        }

def get_default_symbols(config_type: str) -> List[str]:
    """Get default symbols for each config type"""
    defaults = {
        "portfolio": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        "watchlist": ["NVDA", "META", "NFLX", "AMD", "INTC"],
        "us_stocks": ["SPY", "QQQ", "DIA", "VTI", "VOO"],
        "etfs": ["VTI", "VOO", "IVV", "SPY", "QQQ"]
    }
    return defaults.get(config_type, [])

def get_all_local_configs() -> Dict[str, Any]:
    """Get all local configs"""
    configs = {}
    config_types = ["portfolio", "watchlist", "us_stocks", "etfs"]
    
    for config_type in config_types:
        configs[config_type] = load_local_config(config_type)
    
    return {
        "success": True,
        "configs": configs,
        "available_types": config_types
    }

def validate_symbols_local(symbols: List[str]) -> Dict[str, Any]:
    """Validate symbols locally (basic validation)"""
    valid_symbols = []
    invalid_symbols = []
    
    for symbol in symbols:
        # Basic validation: alphanumeric, 1-5 characters
        if isinstance(symbol, str) and len(symbol) >= 1 and len(symbol) <= 5 and symbol.replace('.', '').replace('-', '').isalnum():
            valid_symbols.append(symbol.upper())
        else:
            invalid_symbols.append(symbol)
    
    return {
        "success": True,
        "valid_count": len(valid_symbols),
        "invalid_count": len(invalid_symbols),
        "valid_symbols": valid_symbols,
        "invalid_symbols": invalid_symbols,
        "total_count": len(symbols)
    }
