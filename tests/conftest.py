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
        "USDT",
    ]
)
def token(Token, request):
    tokens = {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
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
        "0xdAC17F958D2ee523a2206206994597C13D831ec7" : "0xF34842d05A1c888Ca02769A633DF37177415C2f8",
    }
    yield interface.IIdleTokenV3_1(idleTokens[token.address])

@pytest.fixture
def tokenWhale(accounts, Contract, token):
    tokenWhalesAndQuantities = {
        "0xdAC17F958D2ee523a2206206994597C13D831ec7" : {
            "whale" : "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", # bitfinex
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

@pytest.fixture
def simpleConverter(strategist, SimpleConverter, uniswap, weth):
    yield SimpleConverter.deploy(
        uniswap,
        weth,
        {"from": strategist}
    )

@pytest.fixture()
def strategy(vault, strategyFactory):
    yield strategyFactory(vault)

@pytest.fixture()
def strategyFactory(strategist, keeper, proxyFactoryInitializable, idleToken, comp, idle, converter, StrategyIdle):
    def factory(vault, proxy=True):
        onBehalfOf = strategist
        govTokens = [
            comp,
            idle,
        ]
        weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        idleReservoir = "0x031f71B5369c251a6544c41CE059e6b3d61e42C6"
        referral = "0x652c1c23780d1A015938dD58b4a65a5F9eFBA653"

        strategyLogic = StrategyIdle.deploy(
            vault,
            govTokens,
            weth,
            idleReservoir,
            idleToken,
            referral,
            converter,
            {"from": strategist}
        )

        strategyAddress = strategyLogic.address

        if proxy:
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

            strategyAddress = (tx.events["ProxyCreated"]["proxy"])

        strategy = StrategyIdle.at(strategyAddress, owner=strategist)
        strategy.setKeeper(keeper)
        return strategy
    yield factory