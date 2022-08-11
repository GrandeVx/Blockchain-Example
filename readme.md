
# Blockchain Example

## Introduction

This is an example of a blockchain. It is a chain of blocks, each of which contains a measurement . The chain is linked by the hashes of the previous blocks. The first block in the chain is called the genesis block. 

## API

    POST /transaction/new
    GET /chain
    POST /nodes/register
    GET /nodes/resolve


## Contribution

This is an Example based on the [Blockchain Tutorial](https://corsi.datamasters.it/products/blockchain-in-python).

    I have added the following features:
        - The chain is stored in a file.
        - the nodes are stored in a file.
        - if the nodes is offline, it was deleted.
