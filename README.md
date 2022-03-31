# pCloud Utilities

This project hosts a number (well, two) of utilities for users of
[pCloud](https://www.pcloud.com).

They are:

`playlist.py`
: Converts m3u playlists to pCloud collection playlists. See the
  [README_playlist.md](https://github.com/mpwillson/pcloud/blob/main/README_playlist.md)
  file for details.

`token.py`
: Manages pCloud authentication tokens. See the
  [README_token.md](https://github.com/mpwillson/pcloud/blob/main/README_token.md)
  file for details.

# COMMON OPTIONS

These options are supported by each pcloud utility:

`-e endpoint`
: Set endpoint for pCloud API.  Default is `https://eapi.pcloud.com`

`-f config-file`
: Set name of configuration file. The default is
  `~/.config/pcloud.json`. If the configuration file does not exist,
  it will be created with the default options. See CONFIGURATION,
  below.

`-r`
: Force login reauthentication. Specify this option if use of the
  existing authentication token produces a 'Login failed' message. The
  auth token may have been deleted from the pCloud server. A username
  (if not already provided in the **config-file**) and password will
  be requested. If a username is not present in the **config-file**,
  the one entered will be saved.

`-u username`
: Set pCloud username. If not set, or the value is empty, a prompt
  will be issued for the username when it is required. The username
  entered will be saved to the **config-file**.

`-v`
: Cause the utility to issue messages on its actions. Default is False.

# CONFIGURATION
The default configuration file is `~/.config/pcloud.json`. Here's an
example with the core configuration options:

``` json
{
  "config-file": "~/.config/pcloud.json",
  "endpoint": "https://eapi.pcloud.com",
  "username": "user@example.com",
  "verbose": false
}

```
Authentication token details will be added to the configuration
file once a successful login is effected. Username and password will
not be requred again, until the authentication token expires (one
year).

The authentication details are held as:

``` json
"auth": {
  "token": "some random string",
  "expires": "Sat Mar 18 21:39:17 2023"
}
```

The configuration file location can be overridden by the **-f**
command option. Options provided on the command line override those
obtained from the configuration file.

If the named **config-file** does not exist, the default internal
configuration options will be written to the file.

Utility programs may add their own specific configuration elements to
the **config-file**. See their README files for details.
