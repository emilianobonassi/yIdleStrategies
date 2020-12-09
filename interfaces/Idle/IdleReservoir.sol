// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;

interface IdleReservoir {
  function drip() external returns (uint256);
}