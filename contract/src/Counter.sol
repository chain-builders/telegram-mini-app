// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract TelegramMiniApp {
    event ETHSent(address sender, address recipient, uint256 amount);
    event TokenSent(address token, address sender, address recipient, uint256 amount);

    // Function to send ETH to another address
    function sendETH(address payable recipient) external payable {
        require(msg.value > 0, "Send some ETH");
        recipient.transfer(msg.value);
        emit ETHSent(msg.sender, recipient, msg.value);
    }

    // Function to send ERC20 tokens to another address
    function sendToken(address tokenAddress, address recipient, uint256 amount) external {
        IERC20 token = IERC20(tokenAddress);
        require(token.transferFrom(msg.sender, recipient, amount), "Transfer failed");
        emit TokenSent(tokenAddress, msg.sender, recipient, amount);
    }
}