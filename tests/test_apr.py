import pytest
import brownie
from brownie import Wei

def stateOfVault(vault, strategy):
    print('\n----state of vault----')
    strState = vault.strategies(strategy)
    totalDebt = strState[6].to('ether')
    totalReturns = strState[7].to('ether')
    print(f'Total Strategy Debt: {totalDebt:.5f}')
    print(f'Total Strategy Returns: {totalReturns:.5f}')
    balance = vault.totalAssets().to('ether')
    print(f'Total Assets: {balance:.5f}')

def stateOfStrat(strategy, token):
    print('\n----state of strat----')
    decimals = token.decimals()
    print(token.symbol(), ':', token.balanceOf(strategy)/(10 ** decimals))
    print('total assets estimate:', strategy.estimatedTotalAssets()/(10 ** decimals))  


def wait(blocks, chain):
    print(f'\nWaiting {blocks} blocks')
    timeN = chain.time()
    endTime = blocks*13 + timeN
    chain.mine(blocks,endTime)

#note you can use real gas prices and estimates here but for testing better to hardcode
def harvest(strategy, keeper, vault, decimals):
    # Evaluate gas cost of calling harvest
    #gasprice = get_gas_price()
    gasprice = 30*1e9
    #txgas = strategy.harvest.estimate_gas()
    txgas = 1500000 #1.5m
    txGasCost = txgas * gasprice
    avCredit = vault.creditAvailable(strategy)
    if avCredit > 0:
        print('Available credit from vault: ', avCredit/(10 ** decimals))
    harvestCondition = strategy.harvestTrigger(txGasCost, {'from': keeper})
    if harvestCondition:
        print('\n----bot calls harvest----')
        print('Tx harvest() gas cost: ', txGasCost/1e18)
        print('Gas price: ', gasprice/1e9)
        strategy.harvest({'from': keeper})

def test_apr(vault, gov, strategy, token, tokenWhale, strategist, keeper, chain, idleToken, aprDeposit):
    decimals = token.decimals()
    token.approve(vault, 2 ** 256 - 1, {"from": tokenWhale})
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    vault.addStrategy(strategy, 10_000, 0, 2 ** 256 - 1, 0, {"from": gov})
    
    vault.deposit(aprDeposit * (10 ** decimals), {"from": tokenWhale})
    idleToken.rebalance({"from": tokenWhale})

    strategy.setProfitFactor(1, {"from": strategist })
    assert(strategy.profitFactor() == 1)

    startingBalance = vault.totalAssets()

    stateOfStrat(strategy, token)
    stateOfVault(vault, strategy)

    for i in range(10):
        
        waitBlock = 100
        print(f'\n----wait {waitBlock} blocks----')
        wait(waitBlock, chain)
        ppsBefore = vault.pricePerShare()
        
        harvest(strategy, strategist, vault, decimals)
        ppsAfter = vault.pricePerShare()

       
        #stateOfStrat(strategy, token)
        #stateOfVault(vault, strategy)

        profit = (vault.totalAssets() - startingBalance)/(10 ** decimals)
        strState = vault.strategies(strategy)
        totalReturns = strState[7]
        totaleth = totalReturns/(10 ** decimals)
        print(f'Real Profit: {profit:.5f}')
        difff= profit-totaleth
        print(f'Diff: {difff}')

        blocks_per_year = 2_300_000
        assert startingBalance != 0
        time =(i+1)*waitBlock
        assert time != 0
        ppsProfit = (ppsAfter - ppsBefore)/(10 ** decimals)/waitBlock*blocks_per_year
        apr = (totalReturns/startingBalance) * (blocks_per_year / time)
        print(f'implied apr assets: {apr:.8%}')
        print(f'implied apr pps: {ppsProfit:.8%}')
    vault.withdraw(vault.balanceOf(tokenWhale), {'from': tokenWhale})