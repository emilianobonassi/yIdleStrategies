import pytest
import brownie
from brownie import Wei
from brownie import config


def test_converter_balancer_weth(converter, accounts, idle, weth):
    user = accounts[0]
    idleWhale = accounts.at('0x107A369bc066c77FF061c7d2420618a6ce31B925', True)

    amount = '100 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(converter, amount, {'from': user})

    balancePre = weth.balanceOf(user)
    tx = converter.convert(amount, 1, idle, weth, user, {'from': user})

    assert tx.events['LOG_SWAP']['tokenAmountIn'] == 100 * (10 ** 18)
    assert tx.events['LOG_SWAP']['tokenAmountOut'] == (weth.balanceOf(user)-balancePre)

    assert weth.balanceOf(converter) == 0
    assert idle.balanceOf(converter) == 0

    amount = '0.005 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(converter, amount, {'from': user})

    balancePre = weth.balanceOf(user)
    tx = converter.convert(amount, 1, idle, weth, user, {'from': user})

    assert tx.events.count('LOG_SWAP') == 0

    assert tx.events['Swap']['amount0In'] == 5000000000000000
    assert tx.events['Swap']['amount1Out'] == (weth.balanceOf(user)-balancePre)

    assert weth.balanceOf(converter) == 0
    assert idle.balanceOf(converter) == 0


def test_converter_balancer_token(Contract, converter, accounts, idle, weth):
    dai = Contract('0x6B175474E89094C44Da98b954EedeAC495271d0F')

    user = accounts[0]
    idleWhale = accounts.at('0x107A369bc066c77FF061c7d2420618a6ce31B925', True)

    amount = '100 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(converter, amount, {'from': user})

    balancePre = dai.balanceOf(user)
    tx = converter.convert(amount, 1, idle, dai, user, {'from': user})

    assert tx.events['LOG_SWAP']['tokenAmountIn'] == 100 * (10 ** 18)
    assert tx.events['LOG_SWAP']['tokenAmountOut'] == tx.events['Swap']['amount1In']
    assert tx.events['Swap']['amount0Out'] == (dai.balanceOf(user)-balancePre)

    assert weth.balanceOf(converter) == 0
    assert idle.balanceOf(converter) == 0
    assert dai.balanceOf(converter) == 0

    amount = '0.005 ether'
    idle.transfer(user, amount, {'from': idleWhale})

    idle.approve(converter, amount, {'from': user})

    balancePre = dai.balanceOf(user)
    tx = converter.convert(amount, 1, idle, dai, user, {'from': user})

    assert tx.events.count('LOG_SWAP') == 0

    assert tx.events['Swap'][0]['amount0In'] == 5000000000000000
    assert tx.events['Swap'][1]['amount0Out'] == (dai.balanceOf(user)-balancePre)

    assert weth.balanceOf(converter) == 0
    assert idle.balanceOf(converter) == 0
    assert dai.balanceOf(converter) == 0