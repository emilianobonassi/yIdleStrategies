import pytest
from brownie import config

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
def token(Token):
    yield Token.at("0x6B175474E89094C44Da98b954EedeAC495271d0F")

@pytest.fixture
def tokenWhale(accounts, Contract, token):
    a = accounts[5]
    binance = accounts.at("0xf977814e90da44bfa03b6295a0616a897441acec", force=True)
    bal = 1e6 * 1e18
    token.transfer(a, bal, {"from": binance})
    yield a

@pytest.fixture
def vault(pm, gov, rewards, guardian, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, token, gov, rewards, "", "")
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
def strategy(strategist, keeper, vault, StrategyIdleDAI_BY):
    strategy = strategist.deploy(StrategyIdleDAI_BY, vault)
    strategy.setKeeper(keeper)
    yield strategy