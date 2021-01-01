import pytest
import brownie
from brownie import Wei
from brownie import config


def test_constructor(vault, gov, strategy, strategist, comp, idle):
    assert strategy.name() == "StrategyIdleidleUSDCYield"
    assert strategy.govTokens(0) == comp
    assert strategy.govTokens(1) == idle

def test_incorrect_vault(pm, guardian, gov, strategist, rewards, strategyFactory, Token):
    token = guardian.deploy(Token)
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, token, gov, rewards, "", "")
    with brownie.reverts("Vault want is different from Idle token underlying"):
        strategy = strategyFactory(vault)

def test_double_init(strategy, strategist):
    with brownie.reverts("You can only initialize once"):
        strategy.init(
            strategist,
            strategist,
            [],
            strategist,
            strategist,
            strategist,
            strategist,
            strategist
        )