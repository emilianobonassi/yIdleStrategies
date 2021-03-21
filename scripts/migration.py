from pathlib import Path

from brownie import StrategyIdle, interface, accounts, config, network, project, web3, rpc

Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault

def migration_usdc_profit_fix():
    assert rpc.is_active()
    ychad = accounts.at(web3.ens.resolve("ychad.eth"), force=True)

    yvusdc = Vault.at("0x5f18C75AbDAe578b483E5F43f12a39cF75b973a9", owner=ychad)
    oldStrategy = "0x157fE71B86AE9200A93054c8d91b5B5d8a7a67F9"
    newStrategy = "0x79B3D0A9513C49D7Ea4BD6868a08aD966eC18f46"
    yvusdc.migrateStrategy(oldStrategy, newStrategy)

    usdc = interface.IERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    idle = interface.IERC20("0x875773784Af8135eA0ef43b5a374AaD105c5D39e")
    comp = interface.IERC20("0xc00e94Cb662C3520282E6f5717214004A7f26888")

    assert usdc.balanceOf(oldStrategy) == 0
    assert idle.balanceOf(oldStrategy) == 0
    assert comp.balanceOf(oldStrategy) == 0

    strategist = accounts.at("0xD0579bc5C0f839ea2BcC79BB127E2F39801903e2", force=True)
    StrategyIdle.at(newStrategy).harvest({"from": strategist})
    assert yvusdc.strategies(newStrategy).dict()['totalLoss'] <= 1

def migration_wbtc_profit_fix():
    assert rpc.is_active()
    ychad = accounts.at(web3.ens.resolve("ychad.eth"), force=True)

    yvwbtc = Vault.at("0xcB550A6D4C8e3517A939BC79d0c7093eb7cF56B5", owner=ychad)
    oldStrategy = "0x39a382ece7534601B218BdD8AdCEA215CBE2440b"
    newStrategy = "0x3E14d864E4e82eD98849Bf666971f39Cf49Ca986"
    yvwbtc.migrateStrategy(oldStrategy, newStrategy)

    wbtc = interface.IERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
    idle = interface.IERC20("0x875773784Af8135eA0ef43b5a374AaD105c5D39e")
    comp = interface.IERC20("0xc00e94Cb662C3520282E6f5717214004A7f26888")

    assert wbtc.balanceOf(oldStrategy) == 0
    assert idle.balanceOf(oldStrategy) == 0
    assert comp.balanceOf(oldStrategy) == 0

    strategist = accounts.at("0xD0579bc5C0f839ea2BcC79BB127E2F39801903e2", force=True)
    StrategyIdle.at(newStrategy).harvest({"from": strategist})
    assert yvwbtc.strategies(newStrategy).dict()['totalLoss'] <= 1