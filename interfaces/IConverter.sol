
// SPDX-License-Identifier: AGPL-3.0

pragma solidity ^0.6.6;

interface IConverter {
    function convert(
        uint amountIn,
        uint amountOutMin,
        address assetIn,
        address assetOut,
        address to
    ) external returns (uint256 convertedAmount);

    function getAmountOut(uint256 amountIn, address assetIn, address assetOut) external view returns (uint256 amountOut);
    function getAmountIn(uint256 amountOut, address assetIn, address assetOut) external view returns (uint256 amountIn);
}