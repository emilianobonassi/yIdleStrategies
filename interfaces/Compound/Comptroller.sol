// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;

interface Comptroller {
  function compAccrued(address user) external view returns (uint256);
}