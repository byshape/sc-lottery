import pytest

from brownie import network, exceptions
from web3 import Web3

from scripts.deploy_lottery import deploy_contract
from scripts.helpful_scripts import (
    fund_with_link, get_account, get_contract, LOCAL_BLOCKCHAIN_ENVIRONMENTS
)


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()
    entrance_fee = lottery.getEntranceFee()
    expected_fee = Web3.toWei(50 / 4600, "ether")
    assert entrance_fee == expected_fee


def test_no_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_start_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()
    account = get_account()
    lottery.startLottery({"from": account})
    assert lottery.lottery_state() == 0  # OPEN


def test_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()

    account = get_account()
    lottery.startLottery({"from": account})
    assert lottery.lottery_state() == 0  # OPEN
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    assert lottery.players(0) == account


def test_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()

    account = get_account()
    lottery.startLottery({"from": account})
    assert lottery.lottery_state() == 0  # OPEN
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    assert lottery.players(0) == account

    fund_with_link(lottery.address)
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2  # CALCULATING_WINNER


def test_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()
    account = get_account()
    lottery.startLottery({"from": account})
    assert lottery.lottery_state() == 0  # OPEN
    entrance_fee = lottery.getEntranceFee()
    lottery.enter({"from": account, "value": entrance_fee})
    lottery.enter({"from": get_account(index=1), "value": entrance_fee})
    lottery.enter({"from": get_account(index=2), "value": entrance_fee})
    lottery.enter({"from": get_account(index=3), "value": entrance_fee})
    assert lottery.players(0) == account
    fund_with_link(lottery.address)
    account_balance = get_account(index=2).balance()
    lottery_balance = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    static_random = 666
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, static_random, lottery.address, {"from": account}
    )
    assert lottery.recentWinner() == get_account(index=2).address
    assert get_account(index=2).balance() == account_balance + lottery_balance
    assert lottery.balance() == 0
    assert lottery.lottery_state() == 1  # CLOSED
