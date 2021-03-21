from pathlib import Path

from brownie import StrategyIdle, ProxyFactoryInitializable, interface, accounts, config, network, project, web3
from eth_utils import is_checksum_address


API_VERSION = config["dependencies"][0].split("@")[-1]
Vault = project.load(
    Path.home() / ".brownie" / "packages" / config["dependencies"][0]
).Vault


def get_address(msg: str) -> str:
    while True:
        val = input(msg)
        if is_checksum_address(val):
            return val
        else:
            addr = web3.ens.address(val)
            if addr:
                print(f"Found ENS '{val}' [{addr}]")
                return addr
        print(f"I'm sorry, but '{val}' is not a checksummed address or ENS")


def main():
    print(f"You are using the '{network.show_active()}' network")
    dev = accounts.load("dev")
    print(f"You are using: 'dev' [{dev.address}]")

    if input("Is there a Vault for this strategy already? y/[N]: ").lower() != "y":
        vault = Vault.at(get_address("Deployed Vault: "))
    else:
        return  # TODO: Deploy one using scripts from Vault project

    strategyLogic = ''
    if input("Is there a Strategy Idle logic deployed? y/[N]: ").lower() != "y":
        if input("Deploy Strategy Idle logic? y/[N]: ").lower() == "y":
            strategyLogic = StrategyIdle.deploy({'from': dev}, publish_source=True)
        else:
            return
    else:
        strategyLogic = StrategyIdle.at(get_address("Deployed StrategyIdle: "))

    # Ask for IdleToken and check underlying is the same of the vault
    idleToken = interface.IIdleTokenV3_1(get_address("Idle Token: "))
    assert idleToken.token() == vault.token()

    # Production mgr
    onBehalfOf = "0xD0579bc5C0f839ea2BcC79BB127E2F39801903e2"

    comp = "0xc00e94Cb662C3520282E6f5717214004A7f26888"
    idle = "0x875773784Af8135eA0ef43b5a374AaD105c5D39e"
    govTokens = [
        comp,
        idle,
    ]

    weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    idleReservoir = "0x031f71B5369c251a6544c41CE059e6b3d61e42C6"
    referral = onBehalfOf
    uniswapRouterV2 = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

    data = strategyLogic.init.encode_input(
        vault,
        onBehalfOf,
        govTokens,
        weth,
        idleReservoir,
        idleToken,
        referral,
        uniswapRouterV2
    )

    print(
        f"""
    Strategy Parameters

       api: {API_VERSION}
     token: {vault.token()}
      name: '{vault.name()}'
    symbol: '{vault.symbol()}'
 init data: {data}
    """
    )
    if input("Deploy Strategy? y/[N]: ").lower() != "y":
        return

    proxyFactoryInitializable = ProxyFactoryInitializable.at('0xfb8246936a26A75E746B1D074Afcc66373792126')

    tx = proxyFactoryInitializable.deployMinimal(
        strategyLogic,
        data,
        {"from": dev, "gas_price": '170 gwei'})

    strategyAddress =  (tx.events["ProxyCreated"]["proxy"])

    print(f"Strategy deployed at {strategyAddress}")