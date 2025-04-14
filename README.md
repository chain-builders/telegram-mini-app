# Kirapod: Unified Web3 Social Wallet & AI Assistant

![Kirapod Banner](https://placeholder.com/1200x400) <!-- Replace with actual banner image -->

## Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technical Architecture](#-technical-architecture)
- [Smart Contract Details](#-smart-contract-details)
- [Development Stack](#-development-stack)
- [Getting Started](#-getting-started)
- [Deployment Guide](#-deployment-guide)
- [Security Features](#-security-features)
- [Hackathon Deliverables](#-hackathon-deliverables)
- [Contributing](#-contributing)
- [Why Base Network?](#-why-base-network)

## 🌐 Project Overview

Kirapod is an innovative multi-platform Web3 solution that combines:
- **Telegram MiniApp**: Full-featured decentralized application with wallet functionality
- **WhatsApp AI Chatbot**: High-performance conversational interface for crypto operations

Both platforms share:
- The same smart contract infrastructure on Base Network
- Identical user flows and functionalities
- Unified backend architecture
- Consistent UI/UX principles

**Core Concept**: Bridge messaging platforms with decentralized finance through social identity abstraction.

## 🚀 Key Features

### Cross-Platform Wallet System
- Single contract address serving both Telegram and WhatsApp interfaces
- WhatsApp provides AI-powered transaction interface (workaround for MiniApp limitations)
- Telegram offers complete MiniApp experience with enhanced UI

### On-Chain Operations
| Feature            | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| Asset Transfers    | Send/receive ETH, ERC20 tokens, and NFTs across both platforms              |
| Crypto Trading     | Buy/sell digital assets with integrated KYC compliance                      |
| Fiat Gateways      | Deposit/withdraw via traditional payment methods                            |
| Multi-Chain Swaps  | Token exchange across all Base Network assets using Uniswap v4              |

### Social Identity Management
mermaid
graph TD
    A[Telegram Username] --> B[ENS Address Creation]
    B --> C(user.kirapod.base.eth)
    C --> D[Persistent Identity]
    D --> E[Transaction History]
    E --> F[Social Graph Analysis]

### Technical Architecture
#### Smart Contract System
- Base Network Deployment: All contracts deployed on Base mainnet

- Core Components:

* AccountFactory.sol (ERC-4337)

* SocialRecovery.sol

* KirapodSwap.sol (Uniswap v4 integration)

* ComplianceModule.sol (KYC/AML)

#### Backend Services
- Node.js API server

- Python AI chatbot engine

- Transaction relayer for gas abstraction

- ENS resolver service

#### Frontend Implementation
- Telegram: Next.js MiniApp with WAGMI integration

- WhatsApp: React-based web interface with chatbot UI

- Shared component library
### Smart Contract Details
#### Contract Address: 0x... <!-- Insert actual address -->

#### Verified on: BaseScan <!-- Insert link -->

#### Key Contracts:

1. KirapodAccount.sol - ERC-4337 compliant smart accounts

2. SocialPay.sol - ENS-based payment routing

3. TipJar.sol - Group chat tipping functionality

4. ComplianceOracle.sol - Chainlink-powered KYC checks

#### Security:

- OpenZeppelin Audited Contracts

- Foundry Test Coverage: 98%

- Mainnet battle-tested since [DATE]

### Development Stack
#### Core Technologies
Smart Contracts: Solidity, Foundry, OpenZeppelin

Frontend: Next.js, TypeScript, WAGMI, Ethers.js

Backend: Node.js, Python, FastAPI

Infrastructure: MiniKit, Push Protocol, ENS

#### Key Libraries
```json
{
    "chain": "base",
    "accountAbstraction": "ERC-4337",
    "swap": "Uniswap v4",
    "oracles": ["Chainlink", "WorldID"],
    "social": ["ENS", "MiniKit"]
}
```

### Getting Started
#### Prerequisites
- Node.js v18+

- Python 3.10+

- Foundry (for contract work)

- Telegram Developer Account

- WhatsApp Business API Access

#### Installation
1. Clone Repository
```bash
Copy
git clone https://github.com/yourrepo/kirapod.git
cd kirapod
```
2. Backend Setup
```bash
Copy
cd backend
npm install
cp .env.example .env # Configure environment variables
npm run dev
```

3. Frontend Setup
```bash
Copy
cd ../frontend
npm install
npm run dev
```

4. AI Chatbot
```bash
Copy
cd ../ai-service
pip install -r requirements.txt
python main.py
```
### Deployment Guide
#### Contract Deployment
```bash
Copy
forge script script/DeployAll.s.sol \
  --rpc-url base_mainnet \
  --broadcast \
  --verify \
  -vvvv \
  --etherscan-api-key $ETHERSCAN_KEY \
  --private-key $DEPLOYER_KEY
  ```
#### Environment Variables
```ini
Copy
# Required for deployment
BASE_RPC_URL=https://mainnet.base.org
DEPLOYER_KEY=your_private_key
ETHERSCAN_API_KEY=your_key
ALCHEMY_API_KEY=your_key

# For production
SENTRY_DSN=your_dsn
MONGO_URI=mongodb://production-db
```
### Security Features
#### Transaction Safeguards
1. #### ENS Validation:

* New account warnings

* Group membership verification

* 60-day interaction history

* Contract address detection

2. #### Compliance Checks:

* Automated KYC verification

* OFAC sanction screening

* Transaction pattern analysis

3. #### Recovery Options:

* Social recovery via verified contacts

* Time-locked withdrawals

* Multi-sig for large transactions

### Hackathon Deliverables
#### Mandatory Requirements

| Requirement          | Implementation Details                          |
|----------------------|------------------------------------------------|
| MiniKit Usage        | Project scaffolding, auth, notifications       |
| Social Integration   | Telegram + WhatsApp payment graph              |
| Base Name Service    | ENS username resolution (user.kirapod.base.eth)|
| Smart Wallets        | ERC-4337 account abstraction                   |

#### Additional Innovations
1. Cross-platform consistency (Telegram + WhatsApp)

2. AI-powered transaction assistance

3. Group chat tipping mechanics

4. Social graph-based security

### Contributing
Kirapod is 100% open-source under MIT License. We welcome contributions:

1. **Fork the repository**  
   `https://github.com/yourrepo/kirapod/fork`

2. **Create your feature branch**  
   ```bash
   git checkout -b feature/AmazingFeature

3. **Commit your changes**
```bash
 (git commit -m 'Add some amazing feature')
 ```

4, Push to the branch
 ```bash
 (git push origin feature/AmazingFeature)
 ```

5. Open a Pull Request

### Why Base Network?
1. **Efficiency**: Low-cost transactions ideal for social payments

2. **Security**: Ethereum-equivalent security model

3. **Ecosystem**: Growing developer community

4. **Interoperability**: Easy bridging to Ethereum mainnet

5. **Future-Proof**: Native Coinbase integrations

### License
© 2025 Kirapod Team