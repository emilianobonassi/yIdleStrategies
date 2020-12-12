import pytest
import brownie
from brownie import Wei
from brownie import config


def test_constructor(vault, gov, strategy, strategist):
    assert strategy.name() == "StrategyIdleUSDC_BY"

def test_incorrect_vault(pm, guardian, gov, strategist, rewards, StrategyIdleUSDC_BY, Token):
    token = guardian.deploy(Token)
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, token, gov, rewards, "", "")
    with brownie.reverts("Vault want is not USDC"):
        strategy = strategist.deploy(StrategyIdleUSDC_BY, vault)
