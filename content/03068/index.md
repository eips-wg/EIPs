---
eip: 3068
title: Precompile for BN256 HashToCurve Algorithms
author: Dr. Christopher Gorman (@chgormanMH)
discussions-to: https://ethereum-magicians.org/t/pre-compile-for-bls/3973
status: Stagnant
type: Standards Track
category: Core
created: 2020-10-23
requires: 198, 1108
---

## Simple Summary
This EIP defines a hash-to-curve precompile for use in BN256
and would allow for cheaper BLS signature verification.

## Abstract
There is currently no inexpensive way to perform BLS signature
verification for arbitrary messages.
This stems from the fact that there is no precompiled contract
in the EVM for a hash-to-curve algorithm for the BN256 elliptic curve.
The gas cost of calling a deterministic hash-to-curve algorithm
written in Solidity is approximately that of one pairing check,
although the latter requires an order of magnitude
more computation.
This EIP remedies this by implementing a hash-to-curve algorithm
for the BN256 G1 curve, which would reduce the cost of
signature verification to essentially that of the pairing check
precompiled contract.
We also include a hash-to-curve algorithm for the BN256 G2 group.

## Motivation
The precompiled contracts in
[EIP-198](../00198.md) and
[EIP-1108](../01108.md)
increased usage of cryptographic operations in the EVM
by reducing the gas costs.
In particular, the cost reduction from
[EIP-1108](../01108.md)
helps increase the use of SNARKs in Ethereum
via an elliptic curve pairing check;
however, a hash-to-curve algorithm enabling arbitrary
BLS signature verification on BN256 in the EVM was noticeably missing.
There is interest in having a precompiled contract which would allow
for signature verification, as noted
[here](https://ethereum-magicians.org/t/pre-compile-for-bls/3973).

At this time, we are able to perform addition, scalar multiplication,
and pairing checks in BN256.
Reducing these costs in
[EIP-1108](../01108.md)
made [ETHDKG](https://github.com/PhilippSchindler/ethdkg),
a distributed key generation protocol in Ethereum,
less expensive.
ETHDKG by itself is useful; however, what it is lacking is
the ability to verify arbitrary BLS signatures.
Creating group signatures by aggregating partial signatures
is one goal of a DKG protocol.
The DKG enables the computation of partial signatures to be
combined into a group signature offline, but there is no
easy way to verify partial signatures or group signatures
in the EVM.

In order to perform BLS signature validation, a hash-to-curve
algorithm is required.
While the MapToGroup method initially discussed in the original BLS
[paper](./assets/weilsigs.pdf)
works in practice, the nondeterministic nature of the algorithm
leaves something to be desired as we would like to bound
the overall computational cost in the EVM.
A deterministic method for mapping to BN curves is given
[here](./assets/latincrypt12.pdf);
in the paper, Fouque and Tibouchi proved their mapping
was indifferentiable from a random oracle.
This gives us the desired algorithm.

## Specification
Here is the pseudocode for the `HashToG1` function:

```
function HashToG1(msg)
    fieldElement0 = HashToBase(msg, 0x00, 0x01)
    fieldElement1 = HashToBase(msg, 0x02, 0x03)
    curveElement0 = BaseToG1(fieldElement0)
    curveElement1 = BaseToG1(fieldElement1)
    g1Element = ECAdd(curveElement0, curveElement1)
    return g1Element
end function
```

Here is the pseudocode for `HashToBase`;
`msg` is the byte slice to be hashed while `dsp1` and `dsp2`
are domain separation parameters.
`fieldPrime` is the prime of the underlying field.

```
function HashToBase(msg, dsp1, dsp2)
    hashResult0 = uint256(Keccak256(dsp1||msg))
    hashResult1 = uint256(Keccak256(dsp2||msg))
    constant = 2^256 mod fieldPrime
    fieldElement0 = hashResult0*constant          mod fieldPrime
    fieldElement1 = hashResult1                   mod fieldPrime
    fieldElement  = fieldElement0 + fieldElement1 mod fieldPrime
    return fieldElement
end function
```

Here is the pseudocode for `BaseToG1`.
All of these operations are performed in the finite field.
`inverse` computes the multiplicative inverse in the underlying
finite field; we have the convention `inverse(0) == 0`.
`is_square(a)` computes the Legendre symbol of the element,
returning 1 if `a` is a square, -1 if `a` is not a square,
and 0 if `a` is 0.
`sqrt` computes the square root of the element in the finite
field; a square root is assumed to exist.
`sign0` returns the sign of the finite field element.

```
function BaseToG1(t)
    # All operations are done in the finite field GF(fieldPrime)
    # Here, the elliptic curve satisfies the equation
    #       y^2 == g(x) == x^3 + curveB
    constant1 = (-1 + sqrt(-3))/2
    constant2 = -3
    constant3 = 1/3
    constant4 = g(1)
    s = (constant4 + t^2)^3
    alpha = inverse(t^2*(constant4 + t^2))
    x1 = constant1 - constant2*t^4*alpha
    x2 = -1 - x1
    x3 = 1 - constant3*s*alpha
    a1 = x1^3 + curveB
    a2 = x2^3 + curveB
    residue1 = is_square(a1)
    residue2 = is_square(a2)
    index = (residue1 - 1)*(residue2 - 3)/4 + 1
    coef1 = ConstantTimeEquality(1, index)
    coef2 = ConstantTimeEquality(2, index)
    coef3 = ConstantTimeEquality(3, index)
    x = coef1*x1 + coef2*x2 + coef3*x3
    y = sign0(t)*sqrt(x^3 + curveB)
    return (x, y)
end function

function sign0(t)
    if t <= (fieldPrime-1)/2
        return 1
    else
        return fieldPrime-1
    end if
end function

function ConstantTimeEquality(a, b)
    # This function operates in constant time
    if a == b
        return 1
    else
        return 0
    end if
end function
```

In `HashToG2`, we first map to the underlying twist curve
and then clear the cofactor to map to G2.
Here is the pseudocode for `HashToG2`:

```
function HashToG2(msg)
    fieldElement00 = HashToBase(msg, 0x04, 0x05)
    fieldElement01 = HashToBase(msg, 0x06, 0x07)
    fieldElement10 = HashToBase(msg, 0x08, 0x09)
    fieldElement11 = HashToBase(msg, 0x0a, 0x0b)
    fieldElement0 = (fieldElement00, fieldElement01)
    fieldElement1 = (fieldElement10, fieldElement11)
    twistElement0 = BaseToTwist(fieldElement0)
    twistElement1 = BaseToTwist(fieldElement1)
    twistElement = ECAdd(twistElement0, twistElement1)
    g2Element = ClearCofactor(twistElement)
    return g2Element
end function

function ClearCofactor(twistElement)
    return ECMul(twistElement, cofactor)
end function
```

Here is the pseudocode for `BaseToTwist`.

```
function BaseToTwist(t)
    # All operations are done in the finite field GF(fieldPrime^2)
    # Here, the twist curve satisfies the equation
    #       y^2 == g'(x) == x^3 + curveBPrime
    constant1 = (-1 + sqrt(-3))/2
    constant2 = -3
    constant3 = 1/3
    constant4 = g'(1)
    s = (constant4 + t^2)^3
    alpha = inverse(t^2*(constant4 + t^2))
    x1 = constant1 - constant2*t^4*alpha
    x2 = -1 - x1
    x3 = 1 - constant3*s*alpha
    a1 = x1^3 + curveBPrime
    a2 = x2^3 + curveBPrime
    residue1 = is_square(a1)
    residue2 = is_square(a2)
    index = (residue1 - 1)*(residue2 - 3)/4 + 1
    coef1 = ConstantTimeEquality(1, index)
    coef2 = ConstantTimeEquality(2, index)
    coef3 = ConstantTimeEquality(3, index)
    x = coef1*x1 + coef2*x2 + coef3*x3
    y = sign0(t)*sqrt(x^3 + curveBPrime)
    return (x, y)
end function
```

## Rationale
The BaseToG1 algorithm is based on the original Fouque and Tibouchi
[paper](./assets/latincrypt12.pdf)
with modifications based on Wahby and Boneh's
[paper](./assets/2019-403_BLS12_H2C.pdf).
There is freedom in choosing the HashToBase function
and this could easily be changed.
Within HashToBase, the particular hashing algorithm
(Keccak256 in our case) could also be modified.
It may be desired to change the call to `sign0`
at the end of BaseToG1 and BaseToTwist with `is_square`,
as this would result in the same deterministic map to curve from the
Fouque and Tibouchi
[paper](./assets/latincrypt12.pdf)
and ensure HashToG1 is indifferentiable from a random oracle;
they proved this result in their paper.
It may be possible to show that switching the `is_square`
call with `sign0` does not affect indifferentiability,
although this has not been proven.

The HashToG2 algorithm follows from the Wahby and Boneh
[paper](./assets/2019-403_BLS12_H2C.pdf).
Algorithms for computing `inverse`, `is_square`, and `sqrt`
in finite field GF(fieldPrime^2) can be found
[here](./assets/2012-685_Square_Root_Even_Ext.pdf).

We now discuss the potential gas cost for the HashToG1
and HashToG2 operations.
On a local machine, ECMul was clocked at 68 microseconds
per operation.
The same machine clocked HashToG1 at 94 microseconds per operation
when hashing 32 bytes into G1 and 105 microseconds per operation
when hashing 1024 bytes into G1.
Given that it currently costs 6000 gas for ECMul, this gives us
an estimated gas cost for HashToG1 at `8500 + len(bytes)`.
Similarly, HashToG2 was clocked at 886 microseconds per operation
when hashing 32 bytes into G2 and 912 microseconds per operation when
hashing 1024 bytes into G2.
This allows us to estimate the gas cost at `80000 + 3*len(bytes)`.

## Backwards Compatibility
There are no backward compatibility concerns.

## Test Cases
TBD

## Implementation
TBD

## Security Considerations
Due to recent [work](./assets/2015-1027_exTNFS.pdf), the
128-bit security promised by the BN256 elliptic curve no longer applies;
this was mentioned in the Cloudflare BN256
[library](https://github.com/cloudflare/bn256).
There has been some discussion on the exact security decrease
from this advancement; see these
[two](./assets/2016-1102_Assessing_NFS_Advances.pdf)
[papers](./assets/2017-334.pdf)
for different estimates.
The more conservative estimate puts the security of BN256 at
100-bits.
While this is likely still out of reach for many adversaries,
it should give us pause.
This reduced security was noted in the recent MadNet
[whitepaper](./assets/madnet.pdf),
and this security concern was partially mitigated by
requiring Secp256k1 signatures of the partial group signatures
in order for those partial signatures to be valid.
Full disclosure: the author of this EIP works for MadHive,
assisted in the development of MadNet, and
helped write the MadNet whitepaper.

The security concerns of the BN256 elliptic curve
affect any operation using pairing check because it is
related to the elliptic curve pairing;
they are independent of this EIP.

## Copyright
Copyright and related rights waived via [CC0](/LICENSE.md).
