"""
Script for deploying and interacting with lottery based on smart contract.
"""
import time

from brownie import config, network, Lottery

from scripts.helpful_scripts import fund_with_link, get_account, get_contract


def get_lottery():
    if len(Lottery) == 0:
        deploy_contract()
    return Lottery[-1]


def deploy_contract():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False)
    )

    print(f"Lottery was deployed: {lottery.address}")
    return lottery


def start_lottery():
    account = get_account()
    lottery = get_lottery()
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)


def enter_lottery():
    account = get_account()
    lottery = get_lottery()
    entrance_fee = lottery.getEntranceFee() + 100000000  # to be sure it will be accepted
    entrance_tx = lottery.enter({"from": account, "value": entrance_fee})
    entrance_tx.wait(1)


def end_lottery():
    account = get_account()
    lottery = get_lottery()
    # send LINK to contract
    funding_tx = fund_with_link(lottery.address)
    funding_tx.wait(1)
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)
    time.sleep(60)  # Waiting for chainlink oracle's random number and calculating winner
    print(f"Winner is: {lottery.recentWinner()}")


def main():
    deploy_contract()
    start_lottery()
    enter_lottery()
    end_lottery()
