import pytest
import brownie
from brownie import Wei

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

def test_operation():
    pass

def test_profit_from_lending(vault, gov, strategy, token, tokenWhale, strategist, chain):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 0, {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    idleYieldToken = strategy.idleYieldToken()

    # Everything should be invested
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)
    assert token.balanceOf(strategy) == 0
    assert (idleBalanceAfterHarvest-idleBalanceBeforeHarvest) == 100 * (10 ** decimals)

    chain.mine(100)

    strategy.harvest({"from": gov})
    totalDebt = vault.strategies(strategy).dict()["totalDebt"]
    estimatedTotalAssets = strategy.estimatedTotalAssets()

    assert totalDebt == estimatedTotalAssets
