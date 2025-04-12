import os
import json
import logging
import time
from web3 import Web3
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)

logger = logging.getLogger(_name_)

load_dotenv(os.path.join(os.path.dirname(_file_), '../.env'))

class BlockchainManager:
    def _init_(self):
        self.alchemy_http_url = os.getenv("ALCHEMY_HTTP_URL")
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.contract_abi_path = os.getenv('CONTRACT_ABI_PATH')
        self.private_key = os.getenv('CONTRACT_OWNER_PRIVATE_KEY')

        self.http_w3 = None
        self.contract = None

    def validate_env_vars(self):
        missing_vars = []
        if not self.alchemy_http_url:
            missing_vars.append("ALCHEMY_HTTP_URL")
        if not self.contract_address:
            missing_vars.append("CONTRACT_ADDRESS")
        if not self.contract_abi_path:
            missing_vars.append("CONTRACT_ABI_PATH")
        if not self.private_key:
            missing_vars.append("CONTRACT_OWNER_PRIVATE_KEY")
        
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
        
    def load_contract_abi(self):
        try:
            with open(self.contract_abi_path, 'r') as f:
                return json.load(f)['abi']
        except FileNotFoundError:
            logger.error(f"ABI file not found at {self.contract_abi_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in ABI file at {self.contract_abi_path}")
            raise

    def initialize_web3_connections(self):
        self.validate_env_vars()
        self.http_w3 = Web3(Web3.HTTPProvider(self.alchemy_http_url))
        contract_abi = self.load_contract_abi()
        self.contract = self.http_w3.eth.contract(
            address=self.http_w3.to_checksum_address(self.contract_address),
            abi=contract_abi
        )
        print('Web3 connections initialized')
        print(self.contract)
    
