import pytest
from brownie import config

@pytest.fixture
def andre(accounts):
    # Andre, giver of tokens, and maker of yield
    yield accounts[0]

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
def vault(pm, gov, rewards, guardian):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', gov, rewards, "", "")
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
def strategy(strategist, keeper, vault, StrategyIdleUSDC_BY):
    strategy = strategist.deploy(StrategyIdleUSDC_BY, vault)
    strategy.setKeeper(keeper)
    yield strategy