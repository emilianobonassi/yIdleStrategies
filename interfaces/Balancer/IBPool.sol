// SPDX-License-Identifier: AGPL-3.0

pragma solidity ^0.6.12;

interface IBPool {
    function swapExactAmountIn(
        address tokenIn,
        uint tokenAmountIn,
        address tokenOut,
        uint minAmountOut,
        uint maxPrice
    )
    external
    returns (uint tokenAmountOut, uint spotPriceAfter);
}