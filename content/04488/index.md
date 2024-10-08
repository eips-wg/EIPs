---
eip: 4488
title: Transaction calldata gas cost reduction with total calldata limit
description: Greatly decreases the gas cost of transaction calldata and simultaneously caps total transaction calldata in a block
author: Vitalik Buterin (@vbuterin), Ansgar Dietrichs (@adietrichs)
discussions-to: https://ethereum-magicians.org/t/eip-4488-transaction-calldata-gas-cost-reduction-with-total-calldata-limit/7555
type: Standards Track
category: Core
status: Stagnant
created: 2021-11-23
---

## Abstract

Decrease transaction calldata gas cost, and add a limit of how much total transaction calldata can be in a block.

## Motivation

Rollups are in the short and medium term, and possibly the long term, the only trustless scaling solution for Ethereum. Transaction fees on L1 have been very high for months and there is greater urgency in doing anything required to help facilitate an ecosystem-wide move to rollups. Rollups are significantly reducing fees for many Ethereum users: Optimism and Arbitrum frequently provide fees that are ~3-8x lower than the Ethereum base layer itself, and ZK rollups, which have better data compression and can avoid including signatures, have fees ~40-100x lower than the base layer.

However, even these fees are too expensive for many users. The long-term solution to the long-term inadequacy of rollups by themselves has always been [data sharding](https://github.com/ethereum/consensus-specs#sharding), which would add ~1-2 MB/sec of dedicated data space for rollups to the chain. However, data sharding will still take a considerable amount of time to finish implementing and deploying. Hence, a short-term solution to further cut costs for rollups, and to incentivize an ecosystem-wide transition to a rollup-centric Ethereum, is desired.

This EIP presents a quick-to-implement short-term solution that also mitigates security risks.

## Specification

| Parameter | Value |
| - | - |
| `NEW_CALLDATA_GAS_COST` | `3` |
| `BASE_MAX_CALLDATA_PER_BLOCK` | `1,048,576` |
| `CALLDATA_PER_TX_STIPEND` | `300` |

Reduce the gas cost of transaction calldata to `NEW_CALLDATA_GAS_COST` per byte, regardless of whether the byte is zero or nonzero.

Add a rule that a block is only valid if `sum(len(tx.calldata) for tx in block.txs) <= BASE_MAX_CALLDATA_PER_BLOCK + len(block.txs) * CALLDATA_PER_TX_STIPEND`.

## Rationale

A natural alternative proposal is to decrease `NEW_CALLDATA_GAS_COST` without adding a limit. However, this presents a security concern: today, the average block size [is 60-90 kB](https://etherscan.io/chart/blocksize), but the _maximum_ block size is `30M / 16 = 1,875,000` bytes (plus about a kilobyte of block and tx overhead). Simply decreasing the calldata gas cost from 16 to 3 would increase the maximum block size to 10M bytes. This would push the Ethereum p2p networking layer to unprecedented levels of strain and risk breaking the network; some previous live tests of ~500 kB blocks a few years ago had already taken down a few bootstrap nodes.

The decrease-cost-and-cap proposal achieves most of the benefits of the decrease, as rollups are unlikely to _dominate_ Ethereum block space in the short term future and so 1.5 MB will be sufficient, while preventing most of the security risk.

Historically, the Ethereum protocol community has been suspicious of multi-dimensional resource limit rules (in this case, gas and calldata) because such rules greatly increase the complexity of the block packing problem that proposers (today miners, post-merge validators) need to solve. Today, proposers can generate blocks with near-optimal fee revenue by simply choosing transactions in highest-to-lowest order of priority fee. In a multi-dimensional world, proposers would have to deal with multi-dimensional constraints. Multi-dimensional knapsack problems are much more complicated than the single-dimensional equivalent, and well-optimized proprietary implementations built by pools may well outperform default open source implementations.

Today, there are two key reasons why this is less of a problem than before:

1. [EIP-1559](../01559.md) means that, at least most of the time, the problem that block proposers are solving is _not_ a knapsack problem. Rather, block proposers are simply including all the transactions they can find with sufficient base fee and priority fee. Hence, naive algorithms will also frequently generate close-to-optimal results.
2. The existence of sophisticated proprietary strategies for miner extractable value (MEV) extraction means that decentralized optimal block production is already in the medium and long term a lost cause. Research is instead going into solutions that separate away the specialization-friendly task of block body generation from the role of a validator ("proposer/builder separation"). Instead of being a fundamental change, two-dimensional knapsack problems today would be merely "yet another" MEV opportunity.

Hence, it's worth rethinking the historical opposition to multi-dimensional resource limits and considering them as a pragmatic way to simultaneously achieve moderate scalability gains while retaining security.

Additionally, the stipend mechanism makes the two-dimensional optimization problem even less of an issue in practice. 90% of all transactions ([sample](./assets/gas_and_calldata_sample.csv) taken from blocks `13500000, 13501000 ... 13529000`) have <300 bytes of calldata. Hence, if a naive transaction selection algorithm overfills the calldata of a block that the proposer is creating, the proposer will still be able to keep adding transactions from 90% of their mempool.

## Backwards Compatibility

This is a backwards incompatible gas repricing that requires a scheduled network upgrade.

Users will be able to continue operating with no changes.

Miners will be able to continue operating with no changes except for a rule to stop adding new transactions into a block when the total calldata size reaches the maximum. However, there are pragmatic heuristics that they could add to achieve closer-to-optimal returns in such cases: for example, if a block fills up to the size limit, they could repeatedly remove the last data-heavy transaction and replace it with as many data-light transactions as possible, until doing so is no longer profitable.

## Security Considerations

The _burst_ data capacity of the chain does not increase as a result of this proposal (in fact, it slightly decreases). However, the _average_ data capacity will increase. This means that the storage requirements of history-storing will go up. A worst-case scenario would be a theoretical long-run maximum of ~1,262,861 bytes per 12 sec slot, or ~3.0 TB per year.

We recommend [EIP-4444](../04444.md) or some similar history expiry proposal be implemented either at the same time or soon after this EIP to mitigate this risk.

## Copyright

Copyright and related rights waived via [CC0](/LICENSE.md).
 
