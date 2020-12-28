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
    yield Token.at("0x57Ab1ec28D129707052df4dF418D58a2D46d5f51")

@pytest.fixture
def tokenWhale(accounts, Contract, token):
    a = accounts[5]
    sDAO = accounts.at("0x49BE88F0fcC3A8393a59d3688480d7D253C37D2A", force=True)
    bal = 1e6 * 1e18
    token.transfer(a, bal, {"from": sDAO})
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
def strategy(strategist, keeper, vault, StrategyIdleSUSD_BY):
    strategy = strategist.deploy(StrategyIdleSUSD_BY, vault)
    strategy.setKeeper(keeper)
    yield strategy