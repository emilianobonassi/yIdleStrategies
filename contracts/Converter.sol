// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;

import {
    SafeERC20,
    SafeMath,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "@openzeppelin/contracts/access/Ownable.sol";

import "../interfaces/Uniswap/IUniswapRouter.sol";

import "../interfaces/IConverter.sol";

import "../interfaces/Balancer/IBPool.sol";

contract Converter is IConverter, Ownable {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address internal uniswap;
    address immutable weth;
    address internal bpool;
    address internal idle;
    uint256 internal minAmountIn;

    constructor(
        address _uniswap,
        address _weth,
        address _bpool,
        address _idle,
        uint256 _minAmountIn
    ) public {
        uniswap = _uniswap;
        weth = _weth;
        bpool = _bpool;
        idle = _idle;
        minAmountIn = _minAmountIn;
    }

    function getUniswap() external view returns (address) {
        return uniswap;
    }

    function getBPool() external view returns (address) {
        return bpool;
    }

    function getMinMountIn() external view returns (uint256) {
        return minAmountIn;
    }

    function convert(
        uint amountIn,
        uint amountOutMin,
        address assetIn,
        address assetOut,
        address to
    ) external override returns (uint convertedAmount) {
        IERC20(assetIn).safeTransferFrom(msg.sender, address(this), amountIn);

        // Balancer has a minAmount to swap otherwise revert with ERR_MATH_APPROX
        if (assetIn == idle && amountIn >= minAmountIn) {
            if (IERC20(assetIn).allowance(address(this), bpool) < amountIn) {
                IERC20(assetIn).safeApprove(bpool, 0);
                IERC20(assetIn).safeApprove(bpool, type(uint256).max);
            }

            // Convert always IDLE to WETH
            (convertedAmount, ) = IBPool(bpool).swapExactAmountIn(
                assetIn,
                amountIn,
                weth,
                amountOutMin,
                type(uint256).max
            );

            // Return immediately in the case assetOut WETH
            // Otw swap with the default method
            if (assetOut == weth) {
                IERC20(weth).safeTransfer(to, convertedAmount);
                return convertedAmount;
            }

            // assetIn becomes weth and amountIn the returned WETH
            assetIn = weth;
            amountIn = convertedAmount;
        }

        if (IERC20(assetIn).allowance(address(this), uniswap) < amountIn) {
            IERC20(assetIn).safeApprove(uniswap, 0);
            IERC20(assetIn).safeApprove(uniswap, type(uint256).max);
        }

        uint[] memory amounts = IUniswapRouter(uniswap).swapExactTokensForTokens(
            amountIn, amountOutMin, _getPath(assetIn, assetOut), to, now.add(1800)
        );

        convertedAmount = amounts[amounts.length.sub(1)];
    }

    function _getPath(address assetIn, address assetOut) internal view returns (address[] memory path) {
        if (assetIn == weth || assetOut == weth) {
            path = new address[](2);
            path[0] = assetIn;
            path[1] = assetOut;
        } else {
            path = new address[](3);
            path[0] = assetIn;
            path[1] = weth;
            path[2] = assetOut;
        }
    }

    function getAmountOut(uint256 amountIn, address assetIn, address assetOut) external override view returns (uint256 amountOut) {
        address[] memory path = _getPath(assetIn, assetOut);
        uint256[] memory amounts = IUniswapRouter(uniswap).getAmountsOut(amountIn, path);
        return amounts[path.length.sub(1)];
    }

    function getAmountIn(uint256 amountOut, address assetIn, address assetOut) external override view returns (uint256 amountIn) {
        address[] memory path = _getPath(assetIn, assetOut);
        uint256[] memory amounts = IUniswapRouter(uniswap).getAmountsIn(amountIn, path);
        return amounts[0];
    }

    function sweep(address _token) external onlyOwner {
        IERC20(_token).safeTransfer(owner(), IERC20(_token).balanceOf(address(this)));
    }
}