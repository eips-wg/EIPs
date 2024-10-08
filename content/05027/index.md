---
eip: 5027
title: Remove the limit on contract code size
description: Change the limit on contract size from 24576 to infinity
author: Qi Zhou (@qizhou)
discussions-to: https://ethereum-magicians.org/t/eip-5027-unlimit-contract-code-size/9010
status: Stagnant
type: Standards Track
category: Core
created: 2022-04-21
requires: 170, 2929, 2930
---


## Abstract

Remove the limit on the contract code size, i.e., only limit the contract code size by block gas limit, with minimal changes to existing code and proper gas metering adjustment to avoid possible attacks.


## Motivation

The motivation is to remove the limit on the code size so that users can deploy a large-code contract without worrying about splitting the contract into several sub-contracts.

With the dramatic growth of dApplications, the functionalities of smart contracts are becoming more and more complicated, and thus, the sizes of newly developed contracts are steadily increasing.  As a result, we are facing more and more issues with the 24576-bytes contract size limit.  Although several techniques such as splitting a large contract into several sub-contracts can alleviate the issue, these techniques inevitably increase the burden of developing/deploying/maintaining smart contracts.

The proposal implements a solution to remove the existing 24576-bytes limit of the code size.  Further, the proposal aims to minimize the changes in the client implementation (e.g., Geth) with
- proper gas metering to avoid abusing the node resources for contract-related opcodes, i.e, `CODESIZE (0x38)/CODECOPY (0x39)/EXTCODESIZE (0x3B)/EXTCODECOPY (0x3C)/EXTCODEHASH (0x3F)/DELEGATECALL (0xF4)/CALL (0xF1)/CALLCODE (0xF2)/STATICCALL (0xFA)/CREATE (0xF0)/CREATE2 (0xF5)`; and
- no change to the existing structure of the Ethereum state.


## Specification

### Parameters

| Constant                  | Value            |
| ------------------------- | ---------------- |
| `FORK_BLKNUM`             | TBD              |
| `CODE_SIZE_UNIT`          | 24576            |
| `COLD_ACCOUNT_CODE_ACCESS_COST_PER_UNIT`  | 2600             |
| `CREATE_DATA_GAS`         | 200              |

If `block.number >= FORK_BLKNUM`, the contract creation initialization can return data with any length, but the contract-related opcodes will take extra gas as defined below:

- For `CODESIZE/CODECOPY/EXTCODESIZE/EXTCODEHASH`, the gas is unchanged.

- For CREATE/CREATE2, if the newly created contract size > `CODE_SIZE_UNIT`, the opcodes will take extra write gas as

`(CODE_SIZE - CODE_SIZE_UNIT) * CREATE_DATA_GAS`.

- For `EXTCODECOPY/CALL/CALLCODE/DELEGATECALL/STATICCALL`, if the contract code size > `CODE_SIZE_UNIT`, then the opcodes will take extra gas as

```
(CODE_SIZE - 1) // CODE_SIZE_UNIT * COLD_ACCOUNT_CODE_ACCESS_COST_PER_UNIT
```

if the contract is not in `accessed_code_in_addresses` or `0` if the contract is in `accessed_code_in_addresses`, where `//` is the integer divide operator, and `accessed_code_in_addresses: Set[Address]` is a transaction-context-wide set similar to `access_addresses` and `accessed_storage_keys`.

When a transaction execution begins, `accessed_code_in_addresses` will include `tx.sender`, `tx.to`, and all precompiles.

When `CREATE/CREATE2/EXTCODECOPY/CALL/CALLCODE/DELEGATECALL/STATICCALL` is called, immediately add the address to `accessed_code_in_addresses`.

## Rationale

### Gas Metering
The goal is to measure the CPU/IO cost of the contract read/write operations reusing existing gas metering so that the resources will not be abused.

- For code-size-related opcodes (`CODESIZE`/`EXTCODESIZE`), we would expect the client to implement a mapping from the hash of code to the size, so reading the code size of a large contract should still be O(1).

- For `CODECOPY`, the data is already loaded in memory (as part of `CALL/CALLCODE/DELEGATECALL/STATICCALL`), so we do not charge extra gas.

- For `EXTCODEHASH`, the value is already in the account, so we do not charge extra gas.

- For `EXTCODECOPY/CALL/CALLCODE/DELEGATECALL/STATICCALL`, since it will read extra data from the database, we will additionally charge `COLD_ACCOUNT_CODE_ACCESS_COST_PER_UNIT` per extra `CODE_SIZE_UNIT`.

- For `CREATE/CREATE2`, since it will create extra data to the database, we will additionally charge `CREATE_DATA_GAS` per extra bytes.


## Backwards Compatibility

All existing contracts will not be impacted by the proposal.

Only contracts deployed before [EIP-170](../00170.md) could possibly be longer than the current max code size, and the reference implementation was able to successfully import all blocks before that fork.

## Reference Implementation

The reference implementation on Geth is available at [0001-unlimit-code-size.patch](./assets/0001-unlimit-code-size.patch).

## Security Considerations
TBD

## Copyright
Copyright and related rights waived via [CC0](/LICENSE.md).


