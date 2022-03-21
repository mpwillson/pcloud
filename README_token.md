# NAME
token.py: List and delete pCloud authentication tokens

# SYNOPSIS
python token.py   [-d token_id] [-e endpoint] [-f config_file]
                  [-l] [-r] [-u username ] [-v]

# DESCRIPTION
`token.py` will list the current set of valid authentication tokens
held by the pCloud server. `token.py` can also delete these tokens,
as identified by their token name.

# OPTIONS
-d token_id
: Deletes token that matches **token_id**.

-e endpoint
: Set endpoint for pCloud API.  Default is `https://eapi.pcloud.com`

-f config_file
: Set name of configuration file. The default is
  `~/.config/pcloud.json`. Configuration files are in JSON
  format. See CONFIGURATION, below.

-l
: List all authentication tokens: id, expires date and name are shown.

-r
: Force login reauthentication. Specify this option if use of the existing
  authentication tooken produces a 'Login failed' message. The auth
  token may have been deleted from the pCloud server.

-u username
: Set pCloud username. This value is required and defaults to ''.

-v
: Cause `token.py` to issue messages on its actions. Default is False.

# NOTES
If `token.py` is using the token deleted by **-d**, it will lose
connection with pCloud, as the token is immediately invalidated.
