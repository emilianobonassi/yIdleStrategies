import pytest
import brownie
from brownie import Wei
from brownie import config


def test_converter_weth(simpleConverter, accounts, idle, weth):
    user = accounts[0]
    idleWhale = accounts.at('0x107A369bc066c77FF061c7d2420618a6ce31B925', True)

    amount = '100 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(simpleConverter, amount, {'from': user})

    balancePre = weth.balanceOf(user)
    tx = simpleConverter.convert(amount, 1, idle, weth, user, {'from': user})

    assert tx.events['Swap']['amount0In'] == 100 * (10 ** 18)
    assert tx.events['Swap']['amount1Out'] == (weth.balanceOf(user)-balancePre)

    assert weth.balanceOf(simpleConverter) == 0
    assert idle.balanceOf(simpleConverter) == 0


def test_converter_token(Contract, simpleConverter, accounts, idle, weth):
    dai = Contract('0x6B175474E89094C44Da98b954EedeAC495271d0F')

    user = accounts[0]
    idleWhale = accounts.at('0x107A369bc066c77FF061c7d2420618a6ce31B925', True)

    amount = '100 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(simpleConverter, amount, {'from': user})

    balancePre = dai.balanceOf(user)
    tx = simpleConverter.convert(amount, 1, idle, dai, user, {'from': user})

    assert tx.events['Swap'][0]['amount0In'] == 100 * (10 ** 18)
    assert tx.events['Swap'][1]['amount0Out'] == (dai.balanceOf(user)-balancePre)

    assert weth.balanceOf(simpleConverter) == 0
    assert idle.balanceOf(simpleConverter) == 0
    assert dai.balanceOf(simpleConverter) == 0

def test_converter_setters(simpleConverter, accounts, idle):
    owner = accounts.at(simpleConverter.owner(), True)

    simpleConverter.setUniswap(idle, {'from': owner})
    assert simpleConverter.getUniswap() == idle.address

    with brownie.reverts("Ownable: caller is not the owner"):
        simpleConverter.setUniswap(idle, {'from': accounts[0]})

def test_sweep(simpleConverter, accounts, idle):
    owner = accounts.at(simpleConverter.owner(), True)
    user = accounts[0]
    idleWhale = accounts.at('0x107A369bc066c77FF061c7d2420618a6ce31B925', True)

    amount = '100 ether'
    idle.transfer(simpleConverter, amount, {'from': idleWhale})

    preBalance = idle.balanceOf(owner)
    simpleConverter.sweep(idle, {'from': owner})
    assert (idle.balanceOf(owner)-preBalance) == 100 * (10 ** 18)

    with brownie.reverts("Ownable: caller is not the owner"):
        simpleConverter.sweep(idle, {'from': user})