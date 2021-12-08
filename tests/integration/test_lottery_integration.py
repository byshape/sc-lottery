import time

import pytest

from brownie import network

from scripts.deploy_lottery import deploy_contract
from scripts.helpful_scripts import (
    fund_with_link, get_account, LOCAL_BLOCKCHAIN_ENVIRONMENTS
)


def test_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_contract()
    account = get_account()
    lottery.startLottery({"from": account})
    assert lottery.lottery_state() == 0  # OPEN
    entrance_fee = lottery.getEntranceFee() + 1000
    lottery.enter({"from": account, "value": entrance_fee})
    lottery.enter({"from": account, "value": entrance_fee})
    assert lottery.players(0) == account
    fund_with_link(lottery.address)
    account_balance = account.balance()
    lottery_balance = lottery.balance()
    lottery.endLottery({"from": account})
    time.sleep(60)
    assert lottery.recentWinner() == account.address
    assert get_account.balance() == account_balance + lottery_balance
    assert lottery.balance() == 0
    assert lottery.lottery_state() == 1  # CLOSED
