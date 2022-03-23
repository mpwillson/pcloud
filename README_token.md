# NAME
token.py: List and delete pCloud authentication tokens

# SYNOPSIS
```
python token.py   [common_options]
                  [ {--delete token-id[,token-id] ... | --list} ]
```

# DESCRIPTION
`token.py` will list the current set of valid authentication tokens
held by the pCloud server. `token.py` can also delete these tokens,
as identified by their token-id.

# OPTIONS
```--delete token-id[,token-id] ...```
: Deletes tokens specified by a list of one or more **token_ids**.

```--list```
: List all authentication tokens: id, expires date and name are shown.

# NOTES
If `token.py` is using the token deleted by **--delete**, it will lose
connection with pCloud, as the token is immediately invalidated.
