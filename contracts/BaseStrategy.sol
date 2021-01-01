// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;

import "./BaseStrategyInitializable.sol";

abstract contract BaseStrategy is BaseStrategyInitializable {
    constructor (address _vault) public BaseStrategyInitializable(_vault, true){}
}