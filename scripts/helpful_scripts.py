"""
This file provides useful scripts for deploy script.
"""
from brownie import (
    accounts, config, network,
    Contract, MockV3Aggregator, VRFCoordinatorMock, LinkToken
)

DECIMALS = 8
STARTING_PRICE = 4600 * 10 ** 8
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
FORKED_BLOCKCHAIN_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]

contract_to_mock = {"eth_usd_price_feed": MockV3Aggregator,
                    "vrf_coordinator": VRFCoordinatorMock,
                    "link_token": LinkToken}


def is_local_chain():
    return network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS or \
           network.show_active() in FORKED_BLOCKCHAIN_ENVIRONMENTS


def get_account(index=None, acc_id=None):
    if index:
        return accounts[index]
    if acc_id:
        return accounts.load(acc_id)
    if is_local_chain():
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


def deploy_mocks(decimals=DECIMALS, starting_price=STARTING_PRICE):
    account = get_account()
    mock_price_feed = MockV3Aggregator.deploy(decimals, starting_price, {"from": account})
    print(f"Price feed deployed: {mock_price_feed}")
    link_token = LinkToken.deploy({"from": account})
    print(f"Link token deployed: {link_token}")
    vrf_coordinator = VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print(f"VRF coordinator deployed: {vrf_coordinator}")


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config if defined,
    otherwise, it will deploy a mock version of that contract, and returns that mock contract.

    :param contract_name (string)
    :return: brownie.network.contract.ProjectContract: The most recently deployed version of
    this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) == 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)

    return contract


def fund_with_link(
    contract_address, account=None, link_token=None,
    amount=100000000000000000  # 0.1 LINK
    ):
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    funding_tx = link_token.transfer(contract_address, amount, {"from": account})
    funding_tx.wait(1)
    return funding_tx
