import pytest
import brownie
from brownie import Wei


def test_increasing_debt_limit(vault, gov, strategy, token, tokenWhale, strategist, chain):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(100 * (10 ** decimals), {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    idleYieldToken = strategy.idleYieldToken()

    # Everything should be invested
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    chain.sleep(10)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)
    assert token.balanceOf(strategy) == 0
    assert (idleBalanceAfterHarvest-idleBalanceBeforeHarvest) == 100 * (10 ** decimals)

    # Should revert because limit reached
    with brownie.reverts():
        vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    # Once the debt limit is increased, strategy should have invested 200 ether
    vault.setDepositLimit(200 * (10 ** decimals), {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)
    assert token.balanceOf(strategy) == 0


def test_decrease_debt_limit(vault, gov, strategy, token, tokenWhale, strategist, interface, Token, chain):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(200 * (10 ** decimals), {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(200 * (10 ** decimals), {"from": tokenWhale})

    idleYieldToken = strategy.idleYieldToken()

    chain.sleep(10)
    # Everything should be invested
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)
    assert token.balanceOf(strategy) == 0
    assert (idleBalanceAfterHarvest-idleBalanceBeforeHarvest) == 200 * (10 ** decimals)

    # Once the debt limit is increased, strategy should have invested 200 ether
    vault.updateStrategyDebtRatio(strategy, 5_000, {"from": gov})
    assert vault.debtOutstanding(strategy) == 100 * (10 ** decimals)
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)

    # Vault should have 100 ether + profit
    strategyProfit = vault.strategies(strategy).dict()["totalGain"]
    assert token.balanceOf(vault) == (100 * (10 ** decimals) + strategyProfit)
    assert token.balanceOf(strategy) == 0
    assert vault.debtOutstanding(strategy) == 0