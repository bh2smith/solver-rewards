"""Fetching Per Order Rewards from Production and Staging Database"""
from pandas import DataFrame
from web3 import Web3


def map_reward(
    amount: float,
    risk_free: bool,
    batch_contains_unsafe_liquidity: bool,
) -> float:
    """
    Converts orderbook rewards based on additional information of
    "risk_free" batches and (un)safe liquidity orders.
    - risk-free are batches contain only user and liquidity orders (i.e. no AMM interactions),
    - liquidity orders are further classified as being safe or unsafe;
        Examples: (unsafe) 0x and just in time orders which carry some revert risk
    """
    if amount > 0 and risk_free and not batch_contains_unsafe_liquidity:
        # Risk Free User Orders that are not contained in unsafe batches 37 COW tokens.
        return 37.0
    return amount


def unsafe_batches(order_df: DataFrame) -> set[str]:
    """
    Filters for tx_hashes corresponding to batches containing "unsafe"
    liquidity orders. These are identified from the order reward dataframe as
    entries with amount = 0 and safe_liquidity = False.
    """
    liquidity = order_df.loc[order_df["amount"] == 0]
    liquidity = liquidity.astype({"safe_liquidity": "boolean"})
    unsafe_liquidity = liquidity.loc[~liquidity["safe_liquidity"]]
    return set(unsafe_liquidity["tx_hash"])


def aggregate_orderbook_rewards(
    per_order_df: DataFrame, risk_free_transactions: set[str]
) -> DataFrame:
    """
    Takes rewards per order and adjusts them based on whether they were part of
    a risk-free settlement or not. After the new amount mapping is complete,
    the results are aggregated by solver as a sum of amounts and additional
    "transfer" related metadata is appended. The aggregated dataframe is returned.
    """

    unsafe_liquidity_batches = unsafe_batches(per_order_df)
    per_order_df["amount"] = per_order_df[
        ["amount", "tx_hash", "safe_liquidity"]
    ].apply(
        lambda x: map_reward(
            amount=x.amount,
            risk_free=x.tx_hash in risk_free_transactions,
            batch_contains_unsafe_liquidity=x.tx_hash in unsafe_liquidity_batches,
        ),
        axis=1,
    )
    result_agg = (
        per_order_df.groupby("solver")["amount"].agg(["count", "sum"]).reset_index()
    )
    del per_order_df  # We don't need this anymore!
    # Add token address to each column
    result_agg["token_address"] = "0xDEf1CA1fb7FBcDC777520aa7f396b4E015F497aB"
    # Rename columns to align with "Transfer" Object
    result_agg = result_agg.rename(
        columns={"sum": "amount", "count": "num_trades", "solver": "receiver"}
    )
    # Convert float amounts to WEI
    result_agg["amount"] = result_agg["amount"].apply(
        lambda x: Web3().toWei(x, "ether")
    )
    return result_agg