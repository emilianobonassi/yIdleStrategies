import pytest
import brownie
from brownie import Wei
from brownie import config


def test_constructor(vault, gov, strategy, strategist, comp, idle, token):
    assert strategy.name() == "StrategyIdleidle"+ token.symbol().upper() + "Yield"
    assert strategy.getGovTokens()[0] == comp
    assert strategy.getGovTokens()[1] == idle

def test_incorrect_vault(pm, guardian, gov, strategist, rewards, strategyFactory, Token):
    token = guardian.deploy(Token)
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "")
    with brownie.reverts("Vault want is different from Idle token underlying"):
        strategy = strategyFactory(vault)

def test_double_init(strategy, strategist):
    with brownie.reverts("Strategy already initialized"):
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

def test_double_init_no_proxy(strategyFactory, vault, strategist):
    strategy = strategyFactory(vault, False)
    with brownie.reverts("Strategy already initialized"):
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

def test_setters(vault, gov, strategy, token, tokenWhale, strategist, converter, guardian):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.setManagement(guardian, {"from": gov})

    strategy.setCheckVirtualPrice(False, {"from": gov})
    assert strategy.checkVirtualPrice() == False

    strategy.setCheckVirtualPrice(True, {"from": gov})
    assert strategy.checkVirtualPrice() == True

    for user in [gov, guardian]:
        for value in [True, False]:
            strategy.setCheckRedeemedAmount(value, {"from": user})
            assert strategy.checkRedeemedAmount() == value

    strategy.enableAllChecks({"from": gov})
    assert strategy.checkVirtualPrice() == True
    assert strategy.checkRedeemedAmount() == True

    strategy.disableAllChecks({"from": gov})
    assert strategy.checkVirtualPrice() == False
    assert strategy.checkRedeemedAmount() == False

    strategy.setRedeemThreshold(2, {"from": guardian})
    assert strategy.redeemThreshold() == 2

    strategy.setRedeemThreshold(3, {"from": gov})
    assert strategy.redeemThreshold() == 3

    govTokens = [token.address]
    strategy.setGovTokens(govTokens, {"from": gov})
    assert strategy.getGovTokens()[0] == govTokens[0]

    strategy.setConverter(converter, {"from": guardian})
    assert strategy.getConverter() == converter

    with brownie.reverts("!authorized"):
        strategy.setCheckVirtualPrice(False, {"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.setCheckRedeemedAmount(False, {"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.enableAllChecks({"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.enableAllChecks({"from": guardian})

    with brownie.reverts("!authorized"):
        strategy.disableAllChecks({"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.disableAllChecks({"from": guardian})

    with brownie.reverts("!authorized"):
        strategy.setRedeemThreshold(4, {"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.setGovTokens(govTokens, {"from": guardian})

    with brownie.reverts("!authorized"):
        strategy.setGovTokens(govTokens, {"from": strategist})

    with brownie.reverts("!authorized"):
        strategy.setConverter(token, {"from": strategist})

    govTokens = [token.address]*(strategy.MAX_GOV_TOKENS_LENGTH() + 1)
    with brownie.reverts("GovTokens too long"):
        strategy.setGovTokens(govTokens, {"from": gov})
