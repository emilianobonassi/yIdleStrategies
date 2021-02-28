import pytest
import brownie
from brownie import Wei


def test_over_redeem(vault, gov, strategy, token, tokenWhale, strategist):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(100 * (10 ** decimals), {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    idleYieldToken = strategy.idleYieldToken()

    # Everything should be invested
    idleBalanceBeforeHarvest = token.balanceOf(idleYieldToken)
    strategy.harvest({"from": gov})
    idleBalanceAfterHarvest = token.balanceOf(idleYieldToken)
    assert token.balanceOf(strategy) == 0
    assert (idleBalanceAfterHarvest-idleBalanceBeforeHarvest) == 100 * (10 ** decimals)

    token.transfer(strategy, 132, {"from": tokenWhale})

    vault.withdraw(vault.balanceOf(tokenWhale)/2, {"from": tokenWhale})  


