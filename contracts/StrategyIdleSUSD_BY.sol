// SPDX-License-Identifier: AGPL-3.0

pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "./StrategyIdle.sol";

/**
* Adds the mainnet addresses to the StrategyIdle
* BY = Best-Yield
*/
contract StrategyIdleSUSD_BY is StrategyIdle {

  address constant public __comp = address(0xc00e94Cb662C3520282E6f5717214004A7f26888);
  address constant public __idle = address(0x875773784Af8135eA0ef43b5a374AaD105c5D39e);
  address constant public __weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
  address constant public __susd = address(0x57Ab1ec28D129707052df4dF418D58a2D46d5f51);

  address constant public __idleReservoir = address(0x031f71B5369c251a6544c41CE059e6b3d61e42C6);
  
  address constant public __idleYieldToken= address(0xF52CDcD458bf455aeD77751743180eC4A595Fd3F);
  address constant public __referral = address(0x652c1c23780d1A015938dD58b4a65a5F9eFBA653);
  address constant public __uniswapRouterV2 = address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);

  constructor(
    address _vault
  )
  StrategyIdle(
        _vault,
        new address[](0),
        __weth,
        __idleReservoir,
        __idleYieldToken,
        __referral,
        __uniswapRouterV2
  )
  public {
    require(address(want) == __susd, "Vault want is not SUSD");

    address[] memory _govTokens = new address[](2);
    _govTokens[0] = __comp;
    _govTokens[1] = __idle;

    _setGovTokens(_govTokens);
  }

  function name() external override pure returns (string memory) {
      return "StrategyIdleSUSD_BY";
  }
}