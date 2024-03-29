from brownie import config

def test_migration(gov, strategyFactory, vault, token, tokenWhale, strategist, chain):
    strategyOld = strategyFactory(vault)

    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.addStrategy(strategyOld, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(100 * (10 ** decimals), {"from": tokenWhale})

    chain.sleep(10)

    strategyOld.harvest({"from": gov})

    estimatedTotalAssetsStrategyOld = strategyOld.estimatedTotalAssets()

    strategyNext = strategyFactory(vault)

    vault.migrateStrategy(strategyOld, strategyNext, {"from": gov})

    estimatedTotalAssetsStrategyNext = strategyNext.estimatedTotalAssets()

    assert estimatedTotalAssetsStrategyNext + 1 >= estimatedTotalAssetsStrategyOld

    strategyNext.harvest({"from": strategist})

    assert vault.strategies(strategyNext).dict()['totalLoss'] <= 1