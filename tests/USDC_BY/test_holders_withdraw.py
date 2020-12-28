import pytest
from brownie import config


def test_holders_withdraw(chain, pm, accounts, StrategyIdleUSDC_BY, token, Token):
    chain.snapshot()
    # get current strategy
    currentyStrategy = StrategyIdleUSDC_BY.at("0x70A23A43113aA4B7a08451421bCA0EFaF2398479")
    strategist = accounts.at(currentyStrategy.strategist(), force=True)

    # seed funds for deployment
    accounts[0].transfer(strategist, "2 ether")

    # get current vault
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at(currentyStrategy.vault())

    # deploy new (fixed) strategy
    newStrategy = strategist.deploy(StrategyIdleUSDC_BY, vault)

    # migrate to new strategy (strategist is gov today)    
    vault.migrateStrategy(currentyStrategy, newStrategy, {"from": strategist})

    # check old strategy is empty
    idleYieldToken = Token.at(currentyStrategy.idleYieldToken())
    comp = Token.at(currentyStrategy.__comp())
    idle = Token.at(currentyStrategy.__idle())

    assert idleYieldToken.balanceOf(currentyStrategy) == 0
    assert comp.balanceOf(currentyStrategy) == 0
    assert idle.balanceOf(currentyStrategy) == 0

    # test withdraw current olders

    holderAddresses = [
        "0x35d8057986e6f96c2ddfa7e8589f1af72d0db1d8",
        "0x441fb640826766e4fdb0769fdc58be2e36126932",
        "0xb3e08599ac57666be68dbb3d311b9c607900a83b",
        "0x29d221385545b1d73afd113cbb07c161cba23885",
        "0x40e652fe0ec7329dc80282a6db8f03253046efde",
        "0xd0579bc5c0f839ea2bcc79bb127e2f39801903e2"
    ]

    tokenDecimals = token.decimals()
    tokenSymbol = token.symbol()
    for holderAddress in holderAddresses:
        holder = accounts.at(holderAddress, force=True)

        balanceHolderBefore = token.balanceOf(holder)
        vault.withdraw({"from": holder})
        balanceHolderAfter = token.balanceOf(holder)
        gainHolder = (balanceHolderAfter-balanceHolderBefore)/(10 ** tokenDecimals)

        print (holderAddress + ':' + ' ' + str(gainHolder) + ' ' + tokenSymbol)

        assert gainHolder > 0
    
    assert token.balanceOf(vault) == 0
    assert idleYieldToken.balanceOf(newStrategy) == 0

    chain.revert()


