// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;

interface IdleController {
  function idleAccrued(address user) external view returns (uint256);
}