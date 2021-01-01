import pytest
import brownie
from brownie import Wei
from brownie import config


def test_constructor(vault, gov, strategy, strategist):
    assert strategy.name() == "StrategyIdleSUSD_BY"
    assert strategy.govTokens(0) == strategy.__comp()
    assert strategy.govTokens(1) == strategy.__idle()

def test_incorrect_vault(pm, guardian, gov, strategist, rewards, StrategyIdleSUSD_BY, Token):
    token = guardian.deploy(Token)
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, token, gov, rewards, "", "")
    with brownie.reverts("Vault want is different from Idle token underlying"):
        strategy = strategist.deploy(StrategyIdleSUSD_BY, vault)
