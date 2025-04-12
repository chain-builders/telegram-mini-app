// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Counter.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("MockToken", "MKT") {
        _mint(msg.sender, 1_000_000 ether);
    }
}

contract TelegramMiniAppTest is Test {
    TelegramMiniApp public app;
    MockERC20 public token;
    address payable public alice;
    address payable public bob;

    function setUp() public {
        app = new TelegramMiniApp();
        token = new MockERC20();

        alice = payable(address(0xA1));
        bob = payable(address(0xB0));

        // Labeling for better test output
        vm.label(alice, "Alice");
        vm.label(bob, "Bob");

        // Give Alice some ETH and tokens
        vm.deal(alice, 10 ether);
        token.transfer(alice, 1_000 ether);
    }

    function testSendETH() public {
        vm.startPrank(alice);
        uint256 initialBalance = bob.balance;

        app.sendETH{value: 1 ether}(bob);

        assertEq(bob.balance, initialBalance + 1 ether);
        vm.stopPrank();
    }

    function testSendETHZeroReverts() public {
        vm.prank(alice);
        vm.expectRevert("Send some ETH");
        app.sendETH{value: 0}(bob);
    }

    function testSendToken() public {
        vm.startPrank(alice);
        token.approve(address(app), 100 ether);

        uint256 initialBalance = token.balanceOf(bob);

        app.sendToken(address(token), bob, 100 ether);

        assertEq(token.balanceOf(bob), initialBalance + 100 ether);
        vm.stopPrank();
    }

    function testSendTokenFailsWithoutApproval() public {
        vm.startPrank(alice);
        vm.expectRevert();
        app.sendToken(address(token), bob, 100 ether);
        vm.stopPrank();
    }
}
