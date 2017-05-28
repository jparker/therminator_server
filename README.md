# Terminator Server

The therminator project is a client/server application I'm developing to log
data about my home. See
[therminator\_client](https://github.com/jparker/therminator_client) for the
client component.

This repository houses the server component.

## Installation

The PostgreSQL database needs to have the pgcrypto extension installed:

```sql
CREATE EXTENSION pgcrypto;
```

## Usage
