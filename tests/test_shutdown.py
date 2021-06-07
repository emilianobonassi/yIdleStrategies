# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes

from brownie import config

def test_emergency_exit(gov, strategyFactory, vault, token, tokenWhale, idleToken, interface, chain):
    strategy = strategyFactory(vault)

    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    chain.sleep(10)

    strategy.harvest({"from": gov})

    strategy.setEmergencyExit({"from": gov})

    strategy.harvest({"from": gov})

    assert interface.IERC20(idleToken).balanceOf(strategy) == 0

    assert token.balanceOf(strategy) == 0
    assert token.balanceOf(vault) >= (100 * (10 ** decimals)) - 1