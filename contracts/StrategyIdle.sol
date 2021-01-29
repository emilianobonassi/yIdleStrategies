// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import {
    BaseStrategyInitializable,
    StrategyParams
} from "./BaseStrategyInitializable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "../interfaces/Idle/IIdleTokenV3_1.sol";
import "../interfaces/Idle/IdleReservoir.sol";
import "../interfaces/Uniswap/IUniswapRouter.sol";

contract StrategyIdle is BaseStrategyInitializable {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    uint256 constant public FULL_ALLOC = 100000;

    address public uniswapRouterV2;
    address public weth;
    address public idleReservoir;
    address public idleYieldToken;
    address public referral;

    bool public checkVirtualPrice;
    uint256 public lastVirtualPrice;

    bool public checkRedeemedAmount;

    bool public alreadyRedeemed;

    address[] public govTokens;

    modifier updateVirtualPrice() {
        uint256 currentTokenPrice = _getTokenPrice();
        if (checkVirtualPrice) {
            require(lastVirtualPrice <= currentTokenPrice, "Virtual price is decreasing from the last time, potential losses");
        }
        lastVirtualPrice = currentTokenPrice;
        _;
    }

    constructor() public BaseStrategyInitializable(address(0), false) {}

    function init(
        address _vault,
        address _onBehalfOf,
        address[] memory _govTokens,
        address _weth,
        address _idleReservoir,
        address _idleYieldToken,
        address _referral,
        address _uniswapRouterV2
    ) external {
        _init(
            _vault,
            _onBehalfOf,
            _govTokens,
            _weth,
            _idleReservoir,
            _idleYieldToken,
            _referral,
            _uniswapRouterV2
        );
    }

    function _init(
        address _vault,
        address _onBehalfOf,
        address[] memory _govTokens,
        address _weth,
        address _idleReservoir,
        address _idleYieldToken,
        address _referral,
        address _uniswapRouterV2
    ) internal {
        _init(_vault, _onBehalfOf);

        require(address(want) == IIdleTokenV3_1(_idleYieldToken).token(), "Vault want is different from Idle token underlying");

        govTokens = _govTokens;
        weth = _weth;
        idleReservoir = _idleReservoir;
        idleYieldToken = _idleYieldToken;
        referral = _referral;

        uniswapRouterV2 = _uniswapRouterV2;

        checkVirtualPrice = true;
        lastVirtualPrice = IIdleTokenV3_1(_idleYieldToken).tokenPrice();

        alreadyRedeemed = false;

        checkRedeemedAmount = true;
    }

    function setCheckVirtualPrice(bool _checkVirtualPrice) external onlyGovernance {
        checkVirtualPrice = _checkVirtualPrice;
    }

    function setCheckRedeemedAmount(bool _checkRedeemedAmount) external onlyGovernance {
        checkRedeemedAmount = _checkRedeemedAmount;
    }

    function enableAllChecks() external onlyGovernance {
        checkVirtualPrice = true;
        checkRedeemedAmount = true;
    }

    function disableAllChecks() external onlyGovernance {
        checkVirtualPrice = false;
        checkRedeemedAmount = false;
    }

    function setGovTokens(address[] memory _govTokens) external onlyGovernance {
        _setGovTokens(_govTokens);
    }

    // ******** OVERRIDE THESE METHODS FROM BASE CONTRACT ************

    function name() external override view returns (string memory) {
        return string(abi.encodePacked("StrategyIdle", IIdleTokenV3_1(idleYieldToken).symbol()));
    }

    function estimatedTotalAssets() public override view returns (uint256) {
        // TODO: Build a more accurate estimate using the value of all positions in terms of `want`
        return want.balanceOf(address(this))
                   .add(balanceOnIdle()) //TODO: estimate gov tokens value
        ;
    }

    /*
     * Perform any strategy unwinding or other calls necessary to capture the "free return"
     * this strategy has generated since the last time it's core position(s) were adjusted.
     * Examples include unwrapping extra rewards. This call is only used during "normal operation"
     * of a Strategy, and should be optimized to minimize losses as much as possible. This method
     * returns any realized profits and/or realized losses incurred, and should return the total
     * amounts of profits/losses/debt payments (in `want` tokens) for the Vault's accounting
     * (e.g. `want.balanceOf(this) >= _debtPayment + _profit - _loss`).
     *
     * NOTE: `_debtPayment` should be less than or equal to `_debtOutstanding`. It is okay for it
     *       to be less than `_debtOutstanding`, as that should only used as a guide for how much
     *       is left to pay back. Payments should be made to minimize loss from slippage, debt,
     *       withdrawal fees, etc.
     */
    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // Reset, it could have been set during a withdrawal
        if(alreadyRedeemed) {
            alreadyRedeemed = false;
        }

        // Assure IdleController has IDLE tokens
        IdleReservoir(idleReservoir).drip();

        // Try to pay debt asap
        if (_debtOutstanding > 0) {
            uint256 _amountFreed = 0;
            (_amountFreed, _loss) = liquidatePosition(_debtOutstanding);
            // Using Math.min() since we might free more than needed
            _debtPayment = Math.min(_amountFreed, _debtOutstanding);
        }

        // Claim only if not done in the previous liquidate step during redeem
        if (!alreadyRedeemed) {
            IIdleTokenV3_1(idleYieldToken).redeemIdleToken(0);
        } else {
            alreadyRedeemed = false;
        }

        // If we have govTokens, let's convert them!
        // This is done in a separate step since there might have been
        // a migration or an exitPosition
        
        // This might be > 0 because of a strategy migration
        uint256 balanceOfWantBeforeSwap = balanceOfWant();
        _liquidateGovTokens();
        _profit = balanceOfWant().sub(balanceOfWantBeforeSwap);
    }

    /*
     * Perform any adjustments to the core position(s) of this strategy given
     * what change the Vault made in the "investable capital" available to the
     * strategy. Note that all "free capital" in the strategy after the report
     * was made is available for reinvestment. Also note that this number could
     * be 0, and you should handle that scenario accordingly.
     */
    function adjustPosition(uint256 _debtOutstanding) internal override updateVirtualPrice {
        // TODO: Do something to invest excess `want` tokens (from the Vault) into your positions
        // NOTE: Try to adjust positions so that `_debtOutstanding` can be freed up on *next* harvest (not immediately)

        //emergency exit is dealt with in prepareReturn
        if (emergencyExit) {
            return;
        }

        uint256 balanceOfWant = balanceOfWant();
        if (balanceOfWant > _debtOutstanding) {
            uint256 _wantAvailable = balanceOfWant.sub(_debtOutstanding);

            want.safeApprove(idleYieldToken, 0);
            want.safeApprove(idleYieldToken, _wantAvailable);
            IIdleTokenV3_1(idleYieldToken).mintIdleToken(_wantAvailable, true, referral);
        }
    }

    /*
     * Liquidate as many assets as possible to `want`, irregardless of slippage,
     * up to `_amountNeeded`. Any excess should be re-invested here as well.
     */
    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        updateVirtualPrice
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        // TODO: Do stuff here to free up to `_amountNeeded` from all positions back into `want`

        if (balanceOfWant() < _amountNeeded) {
            // Note: potential drift by 1 wei, reduce to max balance in the case approx is rounded up
            uint256 valueToRedeemApprox = (_amountNeeded.sub(balanceOfWant())).mul(1e18).div(lastVirtualPrice) + 1;
            uint256 valueToRedeem = Math.min(
                valueToRedeemApprox,
                IERC20(idleYieldToken).balanceOf(address(this))
            );

            alreadyRedeemed = true;
            if (checkRedeemedAmount) {
                uint256 preBalanceOfWant = balanceOfWant();
                IIdleTokenV3_1(idleYieldToken).redeemIdleToken(valueToRedeem);
                uint256 postBalanceOfWant = balanceOfWant();

                // Note: could be equal, prefer >= in case of rounding
                // We just need that is at least the _amountNeeded, not below
                require(
                    (postBalanceOfWant.sub(preBalanceOfWant)) >= _amountNeeded,
                    'Redeemed amount must be >= _amountNeeded');
            } else {
                IIdleTokenV3_1(idleYieldToken).redeemIdleToken(valueToRedeem);
            }
        }

        // _liquidatedAmount min(_amountNeeded, balanceOfWant), otw vault accounting breaks
        uint256 balanceOfWant = balanceOfWant();

        if (balanceOfWant >= _amountNeeded) {
            _liquidatedAmount = _amountNeeded;
        } else {
            _liquidatedAmount = balanceOfWant;
            _loss = _amountNeeded.sub(balanceOfWant);
        }
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function harvestTrigger(uint256 callCost) public view override returns (bool) {
        return super.harvestTrigger(ethToWant(callCost));
    }

    function prepareMigration(address _newStrategy) internal override {
        // TODO: Transfer any non-`want` tokens to the new strategy
        // NOTE: `migrate` will automatically forward all `want` in this strategy to the new one

        // this automatically claims the gov tokens in addition to want
        IIdleTokenV3_1(idleYieldToken).redeemIdleToken(IERC20(idleYieldToken).balanceOf(address(this)));

        // Transfer gov tokens to new strategy
        for (uint256 i = 0; i < govTokens.length; i++) {
            IERC20 govToken = IERC20(govTokens[i]);
            govToken.transfer(_newStrategy, govToken.balanceOf(address(this)));
        }
    }

    function protectedTokens()
        internal
        override
        view
        returns (address[] memory)
    {
        address[] memory protected = new address[](1+govTokens.length);

        for (uint256 i = 0; i < govTokens.length; i++) {
            protected[i] = govTokens[i];
        }
        protected[govTokens.length] = idleYieldToken;

        return protected;
    }

    function balanceOnIdle() public view returns (uint256) {
        return IERC20(idleYieldToken).balanceOf(address(this)).mul(_getTokenPrice()).div(1e18);
    }

    function balanceOfWant() public view returns (uint256) {
        return IERC20(want).balanceOf(address(this));
    }

    function ethToWant(uint256 _amount) public view returns (uint256) {
        if (_amount == 0) {
            return 0;
        }

        address[] memory path = new address[](2);
        path[0] = address(weth);
        path[1] = address(want);
        uint256[] memory amounts = IUniswapRouter(uniswapRouterV2).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];
    }

    function getTokenPrice() view public returns (uint256) {
        return _getTokenPrice();
    }

    function _liquidateGovTokens() internal {
        for (uint256 i = 0; i < govTokens.length; i++) {
            IERC20 govToken = IERC20(govTokens[i]);
            uint256 balance = govToken.balanceOf(address(this));
            if (balance > 0) {
                govToken.safeApprove(uniswapRouterV2, 0);
                govToken.safeApprove(uniswapRouterV2, balance);

                address[] memory path = new address[](3);
                path[0] = address(govToken);
                path[1] = weth;
                path[2] = address(want);

                IUniswapRouter(uniswapRouterV2).swapExactTokensForTokens(
                    balance, 1, path, address(this), now.add(1800)
                );
            }
        }
    }

    function _setGovTokens(address[] memory _govTokens) internal {
        govTokens = _govTokens;
    }

    function _getTokenPrice() view internal returns (uint256) {
        /*
         *  As per https://github.com/Idle-Labs/idle-contracts/blob/ad0f18fef670ea6a4030fe600f64ece3d3ac2202/contracts/IdleTokenGovernance.sol#L878-L900
         *
         *  Price on minting is currentPrice
         *  Price on redeem must consider the fee
         *
         *  Below the implementation of the following redeemPrice formula
         *
         *  redeemPrice := underlyingAmount/idleTokenAmount
         *
         *  redeemPrice = currentPrice * (1 - scaledFee * ΔP%)
         *
         *  where:
         *  - scaledFee   := fee/FULL_ALLOC
         *  - ΔP% := 0 when currentPrice < userAvgPrice (no gain) and (currentPrice-userAvgPrice)/currentPrice
         *
         *  n.b: gain := idleTokenAmount * ΔP% * currentPrice
         */

        IIdleTokenV3_1 iyt = IIdleTokenV3_1(idleYieldToken);

        uint256 userAvgPrice = iyt.userAvgPrices(address(this));
        uint256 currentPrice = iyt.tokenPrice();

        uint256 tokenPrice;

        // When no deposits userAvgPrice is 0 equiv currentPrice
        // and in the case of issues
        if (userAvgPrice == 0 || currentPrice < userAvgPrice) {
            tokenPrice = currentPrice;
        } else {
            uint256 fee = iyt.fee();

            tokenPrice = ((currentPrice.mul(FULL_ALLOC))
                .sub(
                    fee.mul(
                         currentPrice.sub(userAvgPrice)
                    )
                )).div(FULL_ALLOC);
        }

        return tokenPrice;
    }
}
