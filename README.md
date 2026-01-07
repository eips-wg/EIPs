# EIPs vs. ERCs

> [!IMPORTANT]
> Please direct application-level proposals (ERCs) to [`ethereum/ERCs`] and all
> other proposals (EIPs) to [`ethereum/EIPs`].

# Ethereum Improvement Proposals (EIPs)

The EIP project standardizes and provides high-quality documentation for
Ethereum itself and conventions built upon it. This repository tracks past and
ongoing improvements to Ethereum in the form of Ethereum Improvement
Proposals (EIPs). [EIP-1] governs how EIPs are published.

## Taxonomy

The [status page][status] tracks and lists EIPs, which can be divided into the
following types and categories:

- [Core EIPs] are improvements to the Ethereum consensus protocol.
- [Networking EIPs] specify the peer-to-peer networking layer of Ethereum.
- [Interface EIPs] standardize interfaces to Ethereum, which determine how
  users and applications interact with the blockchain.
- [ERCs] specify application layer standards, which determine how applications
  running on Ethereum can interact with each other.
- [Meta EIPs] are miscellaneous improvements that nonetheless require some sort
  of consensus.
- [Informational EIPs] are non-standard improvements that do not require any
  form of consensus.

## Contributing

> [!WARNING]
> Before you write an EIP, ideas MUST be thoroughly discussed on
> [Ethereum Magicians][ethmag] or [Ethereum Research][ethres]. Once consensus
> is reached, thoroughly read and review [EIP-1], which describes the EIP
> process.

To create a new proposal, **copy** the [Proposal Template][template] into the
[`contents`] directory and rename it to `99999.md` (or `99999/index.md` if you
have additional assets). The template has more detailed instructions.

This repository is for documenting standards and not for help implementing
them. These types of inquiries should be directed to the
[Ethereum Stack Exchange][ethex]. For specific questions and concerns regarding
EIPs, it's best to comment on the relevant discussion thread of the EIP denoted
by the `discussions-to` tag in the EIP's preamble.

If you would like to become an EIP Editor, please read [EIP-5069].

### Validation and Auto-merging

All pull requests in this repository must pass checks before they can be
automatically merged:

- [eip-review-bot] determines when PRs can be automatically merged [^1]
- EIP-1 rules are enforced using [`eipw`] [^2]
- Markdown best practices are checked using [markdownlint] [^2]

### Building Locally

It is possible to run the above checks and preview how proposals will render
using [`build-eips`]. See its documentation for more details.

## Preferred Citation Format

The canonical URL for an EIP that has achieved draft status at any point is at
<https://eips.ethereum.org/>. For example, the canonical URL for EIP-1 is
<https://eips.ethereum.org/1/>.

Consider any document not published at <https://eips.ethereum.org/> as a
working paper. Additionally, consider published EIPs with a status of "draft",
"review", or "last call" to be incomplete drafts, and note that their
specification is likely to be subject to change.

[^1]: <https://github.com/ethereum/EIPs/blob/master/.github/workflows/auto-review-bot.yml>
[^2]: <https://github.com/ethereum/EIPs/blob/master/.github/workflows/ci.yml>

[`build-eips`]: https://github.com/ethereum/build-eips
[markdownlint]: https://github.com/DavidAnson/markdownlint
[`eipw`]: https://github.com/ethereum/eipw
[eip-review-bot]: https://github.com/ethereum/eip-review-bot/
[`ethereum/ERCs`]: https://github.com/ethereum/ERCs
[`ethereum/EIPs`]: https://github.com/ethereum/EIPs
[EIP-1]: https://eips.ethereum.org/1/
[ethmag]: https://ethereum-magicians.org/
[ethres]: https://ethresear.ch/t/read-this-before-posting/8
[template]: https://github.com/ethereum/EIPs/blob/master/docs/template.md
[`contents`]: https://github.com/ethereum/EIPs/tree/master/contents
[ethex]: https://ethereum.stackexchange.com
[status]: https://eips.ethereum.org/
[Core EIPs]: https://eips.ethereum.org/category/core/
[Networking EIPs]: https://eips.ethereum.org/category/networking/
[Interface EIPs]: https://eips.ethereum.org/category/interface/
[ERCs]: https://eips.ethereum.org/category/erc/
[Meta EIPs]: https://eips.ethereum.org/type/meta/
[Informational EIPs]: https://eips.ethereum.org/type/informational/
[EIP-5069]: https://eips.ethereum.org/5069/
