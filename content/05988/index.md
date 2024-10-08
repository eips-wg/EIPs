---
eip: 5988
title: Add Poseidon hash function precompile
description: Add a precompiled contract which implements the hash function used in the Poseidon cryptographic hashing algorithm
author: Abdelhamid Bakhta (@abdelhamidbakhta), Eli Ben Sasson (@Elistark), Avihu Levy (@avihu28), David Levit Gurevich (@DavidLevitGurevich)
discussions-to: https://ethereum-magicians.org/t/eip-5988-add-poseidon-hash-function-precompile/11772
status: Stagnant
type: Standards Track
category: Core
created: 2022-11-15
---

## Abstract

This EIP introduces a new precompiled contract which implements the hash function used in the Poseidon cryptographic hashing algorithm, for the purpose of allowing interoperability between the EVM and ZK / Validity rollups, as well as introducing more flexible cryptographic hash primitives to the EVM.

## Motivation

[Poseidon](./assets/papers/poseidon_paper.pdf) is an arithmetic hash function that is designed to be efficient for Zero-Knowledge Proof Systems.
Ethereum adopts a rollup centric roadmap and hence must adopt facilities for L2s to be able to communicate with the EVM in an optimal manner.

ZK-Rollups have particular needs for cryptographic hash functions that can allow for efficient verification of proofs.

The Poseidon hash function is a set of permutations over a prime field, which makes it particularly well-suited for the purpose of building efficient ZK / Validity rollups on Ethereum.

Poseidon is one of the most efficient hashing algorithms that can be used in this context.
Moreover it is compatible with all major proof systems (SNARKs, STARKs, Bulletproofs, etc...).
This makes it a good candidate for a precompile that can be used by many different ZK-Rollups.

An important point to note is that ZK rollups using Poseidon have chosen different sets of parameters, which makes it harder to build a single precompile for all of them.

However, we can still build a generic precompile that supports arbitrary parameters, and allow the ZK rollups to choose the parameters they want to use.

This is the approach that we have taken in this EIP.

## Specification

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

### Parameters

| Constant                      | Value |
| ----------------------------- | ----- |
| `FORK_BLKNUM`                 | `TBD` |
| `GAS_COST`                    | `TBD` |
| `POSEIDON_PRECOMPILE_ADDRESS` | `0xA` |

Here are the Poseidon parameters that the precompile will support:

| Parameter name   | Description                                                        | Encoding size (in bytes) | Comments |
| ---------------- | ------------------------------------------------------------------ | ------------------------ | -------- |
| `p`              | Prime field modulus                                                | 32                       |          |
| `security_level` | Security level measured in bits. Denoted `M` in the Poseidon paper | 2                        |          |
| `alpha`          | Power of S-box                                                     | 1                        |          |
| `input_rate`     | Size of input                                                      | 2                        |          |
| `t`              | Size of the state                                                  | 1                        |          |
| `full_round`     | Number of full rounds. Denoted as `R_F` in the Poseidon paper.     | 1                        |          |
| `partial_round`  | Number of partial rounds. Denoted as `R_P` in the Poseidon paper.  | 1                        |          |
| `input`          | Input to the hash function                                         | `input_rate` * 32        |          |

The encoding of the precompile input is the following:

```
[32 bytes for p][2 bytes for security_level][1 byte for alpha][2 bytes for input_rate][1 byte for t][1 byte for full_round][1 byte for partial_round][input_rate * 32 bytes for input]
```

The precompile should compute the hash function as [specified in the Poseidon paper](./assets/papers/poseidon_paper.pdf) and return hash output.

<!--### Example Usage in Solidity

The precompile can be wrapped easily in Solidity to provide a more development-friendly interface to `poseidon_hash` function.

```solidity
// TODO: Add solidity example
```-->

<!--### Gas Costs

```
TODO: Fill gas costs section
```-->

## Rationale

TODO: Add rationale

TODO: Add rationale for gas cost e.g. benchmark and computation cost estimation.

## Backwards Compatibility

There is very little risk of breaking backwards-compatibility with this EIP, the sole issue being if someone were to build a contract relying on the address at `0xPOSEIDON_PRECOMPILE_ADDRESS` being empty. The likelihood of this is low, and should specific instances arise, the address could be chosen to be any arbitrary value with negligible risk of collision.

## Test Cases

The Poseidon reference implementation contains test vectors that can be used to test the precompile.
Those tests are available [here](./assets/test/poseidon/test_vectors.txt).

<!--## Reference Implementation

TODO: Add initial Geth implementation-->

## Security Considerations

Quoting Vitalik Buterin from `Arithmetic hash based alternatives to KZG for proto-danksharding` thread on EthResearch:

> The Poseidon hash function was officially introduced in 2019. Since then it has seen considerable attempts at cryptanalysis and optimization. However, it is still very young compared to popular “traditional” hash functions (eg. SHA256 and Keccak), and its general approach of accepting a high level of algebraic structure to minimize constraint count is relatively untested.
> There are layer-2 systems live on the Ethereum network and other systems that already rely on these hashes for their security, and so far they have seen no bugs for this reason. Use of Poseidon in production is still somewhat “brave” compared to decades-old tried-and-tested hash functions, but this risk should be weighed against the risks of proposed alternatives (eg. pairings with trusted setups) and the risks associated with centralization that might come as a result of dependence on powerful provers that can prove SHA256.

It is true that arithmetic hash functions are relatively untested compared to traditional hash functions.
However, Poseidon has been thoroughly tested and is considered secure by multiple independent research groups and layers 2 systems are already using it in production (StarkWare, Polygon, Loopring) and also by other projects (e.g. Filecoin).

Moreover, the impact of a potential vulnerability in the Poseidon hash function would be limited to the rollups that use it.

We can see the same rationale for the KZG ceremony in the [EIP-4844](../04844.md), arguing that the risk of a vulnerability in the KZG ceremony is limited to the rollups that use it.

List of projects (non exhaustive) using Poseidon:

- StarkWare plans to use Poseidon as the main hash function for StarkNet, and to add a Poseidon built-in in Cairo.
- Filecoin employs POSEIDON for Merkle tree proofs with different arities and for two-value commitments.
- Dusk Network uses POSEIDON to build a Zcash-like protocol for securities trading.11 It also uses POSEIDON
  for encryption as described above.
- Sovrin uses POSEIDON for Merkle-tree based revocation.
- Loopring uses POSEIDON for private trading on Ethereum.
- Polygon uses Poseidon for Hermez ZK-EVM.

In terms of security, the choice of parameters is important.

### Security of the Poseidon parameters

#### Choice of the MDS matrix

The MDS matrix is a square matrix of size `t` \* `t` that is used to mix the state.

This matrix is used during the `MixLayer` phase of the Poseidon hash function.

The matrix must be chosen s.t. no subspace trail with inactive/active S-boxes can be set up for more than `t -1` rounds.

There are some efficient algorithms to detect weak MDS matrices.

Those algorithms are described in the [Proving Resistance Against Infinitely Long Subspace Trails: How to Choose the Linear Layer](./assets/papers/proving_resistance_linear_layer.pdf) paper.

The process of the generation of the matrix should look like this, as recommended in the Poseidon paper:

1. Generate a random matrix.
2. Check if the matrix is secure using Algorithm 1, Algorithm 2, and Algorithm 3 provided [Proving Resistance Against Infinitely Long Subspace Trails: How to Choose the Linear Layer](./assets/papers/proving_resistance_linear_layer.pdf) paper.
3. If the matrix is not secure, go back to step 1.

### Papers and research related to Poseidon security

- [Poseidon: A New Hash Function for Zero-Knowledge Proof Systems](./assets/papers/poseidon_paper.pdf)
- [Security of the Poseidon Hash Function Against Non-Binary Differential and Linear Attacks](./assets/papers/security_poseidon_non_binary_differential_attacks.pdf)
- [Report on the Security of STARK-friendly Hash Functions](./assets/papers/report_security_stark_friendly_hash.pdf)
- [Practical Algebraic Attacks against some Arithmetization-oriented Hash Functions](./assets/papers/practical_algebraic_attacks.pdf)

## Copyright

Copyright and related rights waived via [CC0](/LICENSE.md).
