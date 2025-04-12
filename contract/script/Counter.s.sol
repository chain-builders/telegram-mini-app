// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "../src/Counter.sol";

contract DeployTelegramMiniApp is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);

        TelegramMiniApp app = new TelegramMiniApp();
        console2.log("TelegramMiniApp deployed at:", address(app));

        vm.stopBroadcast();
    }
}
