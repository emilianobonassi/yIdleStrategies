import pytest
from brownie import config, Wei

@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]

@pytest.fixture
def proxyFactoryInitializable(accounts, ProxyFactoryInitializable):
    yield accounts[0].deploy(ProxyFactoryInitializable)

@pytest.fixture(
    params=[
        "DAI",
        "USDC",
    ]
)
def token(Token, request):
    tokens = {
        "DAI":  "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    }
    yield Token.at(tokens[request.param])

@pytest.fixture
def comp(Token):
    yield Token.at("0xc00e94Cb662C3520282E6f5717214004A7f26888")

@pytest.fixture
def idle(Token):
    yield Token.at("0x875773784Af8135eA0ef43b5a374AaD105c5D39e")

@pytest.fixture
def uniswap(Contract):
    yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

@pytest.fixture
def weth(Contract):
    yield Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

@pytest.fixture
def bpool(Contract):
    yield Contract("0xCaf467DFE064a1F54e4ece8515Ddf326B9bE801E")

@pytest.fixture
def idleToken(interface, token):
    idleTokens = {
        "0x6B175474E89094C44Da98b954EedeAC495271d0F" : "0x3fE7940616e5Bc47b0775a0dccf6237893353bB4",
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" : "0x5274891bEC421B39D23760c04A6755eCB444797C",
    }
    yield interface.IIdleTokenV3_1(idleTokens[token.address])

@pytest.fixture
def tokenWhale(accounts, Contract, token):
    tokenWhalesAndQuantities = {
        "0x6B175474E89094C44Da98b954EedeAC495271d0F" : {
            "whale" : "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf", # matic
            "quantity": 1 * 1e6,
        },
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" : {
            "whale" : "0xf977814e90da44bfa03b6295a0616a897441acec", # binance
            "quantity": 1 * 1e6,
        },
    }

    user = accounts[5]
    tokenWhaleAndQuantity = tokenWhalesAndQuantities[token.address]
    
    whale = accounts.at(tokenWhaleAndQuantity["whale"], force=True)
    bal = tokenWhaleAndQuantity["quantity"] * 10 ** token.decimals()
    token.transfer(user, bal, {"from": whale})

    yield user

@pytest.fixture
def vault(pm, gov, rewards, guardian, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "")
    yield vault


@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]

@pytest.fixture
def converter(strategist, Converter, uniswap, weth, bpool, idle):
    yield Converter.deploy(
        uniswap,
        weth,
        bpool,
        idle,
        "0.01 ether",
        {"from": strategist}
    )

@pytest.fixture()
def strategyLogic(strategist, StrategyIdle):
    yield strategist.deploy(StrategyIdle)

@pytest.fixture()
def strategy(vault, strategyFactory):
    yield strategyFactory(vault)

@pytest.fixture()
def strategyFactory(strategist, keeper, strategyLogic, proxyFactoryInitializable, idleToken, comp, idle, converter, StrategyIdle):
    def factory(vault):
        onBehalfOf = strategist
        govTokens = [
            comp,
            idle,
        ]
        weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        idleReservoir = "0x031f71B5369c251a6544c41CE059e6b3d61e42C6"
        referral = "0x652c1c23780d1A015938dD58b4a65a5F9eFBA653"

        data = strategyLogic.init.encode_input(
            vault,
            onBehalfOf,
            govTokens,
            weth,
            idleReservoir,
            idleToken,
            referral,
            converter
        )

        tx = proxyFactoryInitializable.deployMinimal(
            strategyLogic,
            data,
            {"from": strategist})

        strategyAddress =  (tx.events["ProxyCreated"]["proxy"])
        strategy = StrategyIdle.at(strategyAddress, owner=strategist)
        strategy.setKeeper(keeper)
        return strategy
    yield factory