# putil - pCloud Utilities

**IMPORTANT**

In mid-April 2026, pCloud removed the username/password authentication
mechanism and also invalidated any existing auth tokens.  The OAUTH2
authentication method is now the only method available for pCloud
apps. However, the access_token granted by the OAUTH2 process does not
work with many of the API methods, notably those related to the
handling of collections.  This means that both playlist.py and
token.py do not work anymore. There has been no indication from pCloud
that this situation will change.

## Utilities

This project hosts a number (well, three and only one works) of
utilities for users of [pCloud](https://www.pcloud.com).

They are:

`playlist.py`
: Converts m3u playlists to pCloud collection playlists. See the
  [README_playlist.md](https://github.com/mpwillson/pcloud/blob/main/README_playlist.md)
  file for details. DOES NOT WORK.

`token.py`
: Manages pCloud authentication tokens. See the
  [README_token.md](https://github.com/mpwillson/pcloud/blob/main/README_token.md)
  file for details. DOES NOT WORK.

`pcutil.py`
: Provides cp and rm utilties.  cp copies files to and from pCloud and
  local storage.  rm deletes files and folders from pCloud. See the
  [README_pcutil.md](https://github.com/mpwillson/pcloud/blob/main/README_pcutil.md)
  file for details.


## REQUIREMENTS

- Requires Python version 3.8 or later.
- Operates on UNIX platforms (Linux, FreeBSD).

## COMMON OPTIONS

These options are supported by each pcloud utility:

`-e endpoint`
: Set endpoint for pCloud API.  Default is `https://eapi.pcloud.com`
  for Europe. See below.

`-f config-file`
: Set name of configuration file. The default is
  `~/.config/pcloud.json`. If the configuration file does not exist,
  it will be created with the default options. See CONFIGURATION,
  below.

`-r`
: Force OAUTH2 reauthentication.

`-s`
: Save options specified on command line to the configuration file
  **config-file**. The options include those supported by a utility.

`-t timeout`
: Set timeout for connections to the pCloud endpoint. Default value is 2,
  which equates to approximately 10 seconds.

`-u username`
: Set pCloud username. If not set, or the value is empty, a prompt
  will be issued for the username when it is required. The username
  entered will be saved to the **config-file**.

`-v`
: Cause the utility to issue messages on its actions. Default is False.

## AUTHENTICATION
Authentication via OAUTH2 will be invoked the first time a pCloud app
is run or if the `-r` option is provided. The authentication process
requires a browser, so must be invoked within GUI session. The pCloud
Authorisation page will request your login details (if not cached) and
ask your permission to allow the `putil` app to access your pCloud
files.

If you grant access, pCloud will provide an authentication code, which
the `putil` app prompts for. Once entered, `putil` then requests an
access token from pCloud. If successful, the access token is stored in
the `putil` configuration file.

## CONFIGURATION
The default configuration file is `~/.config/pcloud.json`. Here's an
example with the core configuration options:

``` json
{
  "config-file": "~/.config/pcloud.json",
  "endpoint": "https://eapi.pcloud.com",
  "access_token": "",
  "binary-api-port": 8399,
  "timeout": 2,
  "client-id": "randomID",
  "verbose": false
}

```

The configuration file location can be overridden by the **-f**
command option. Options provided on the command line override those
obtained from the configuration file.

If the named **config-file** does not exist, the default internal
configuration options will be written to the file.

Utility programs may add their own specific configuration elements to
the **config-file**. See their README files for details.

### Endpoint Setting

pCloud has two datacenters; one in United States and one in Europe.

As a consequence API calls must be made to the correct API endpoint
name, which depends on where the user has been registered. If the United
States, use **https://api.pcloud.com**. For Europe, use
**https://eapi.pcloud.com**.
