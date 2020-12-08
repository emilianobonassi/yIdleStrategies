import pytest
import brownie
from brownie import Wei


def test_constructor(vault, gov, strategy, strategist):
    assert strategy.name() == "StrategyIdleUSDC_BY"