# Natter (Legacy)

A web chat from an earlier, more primitive time.

> ## ⚠️ Caution ⚠️
> The core of this code was written in the late 1990s to early 2000s.  It does not represent modern practices.  Do not use this code as inspiration.  Do not do what it does, like using a flat text file a database, or storing passwords as unsalted MD5 hashes.  Do not use this code without professional oversight and thorough code review, and honestly, don't even use it *then*.
>
> This code was not designed to protect against people that know how it works.  Mischievous and clever users may be able to get away with things that they otherwise might not.  This was a feature at the time.

## Requirements

 - Perl 5 with the following modules installed at the system level:
   - `CGI`
   - `Digest::MD5`
   - `DBI`
   - `DBD::SQLite`
 - PHP with the PDO and PDO_SQLITE extensions.
   - Last tested under PHP 7.3, but there are no actual tests here so good luck.
 - The `sqlite3` binary.
 - A web server that will run Perl CGI scripts.
 - A server environment that allows Perl CGI scripts to write files in the directory that they're being executed from.
   - If you are using SELinux, have `audit2why` handy and remember that `setsebool` doesn't persist changes by default.
   - If you are wise enough to use SELinux in Enforcing mode and are still considering using this code, I really don't know what to tell you.
 - The ability to change file and directory ownership and permissions.
   - The messages file, the bans file, the logs directory, and the database directory must be owned by the user executing the CGI script, which is almost always going to be the user running the HTTP server, not the user that owns the file.
 - A web hosting provider that doesn't mind refresh-based web chats.  Check your host's terms of service.  There was a blanket ban on these things on shared hosts back in the late 1990s and early 2000s when this code was created.

 ## Installation

> ## ⚠️️ Caution ⚠️
> This is a bad idea and you shouldn't do it.

1. Place the contents of the repository inside a directory that lives underneath your web root directory.
   - You could probably run this inside the root itself, not a directory under the root.  Probably.  Not gonna lie, I'm not testing this.
2. Copy `config.cgi.default` to `config.cgi`
   - Edit `baseurl`, `basepath`, and `pubdirname` to match reality.
   - `basepath` is *always* your web root directory.
   - Don't touch anything else here for now.
3. Copy `config.inc.php.default` to `config.inc.php`
   - Make the same `baseurl`, `basepath`, and `pubdirname` changes to this file as you made to `config.cgi`
4. Create a file named `messages.html`, containing one newline (CR or CRLF).  Set permissions and ownership on this file to allow the user executing CGI scripts to read and write to it.
5. Create a file named `messages_bans.cgi`, containing one newline (CR or CRLF).  Set permissions and ownership on this file to allow the user executing CGI scripts to read and write to it.
6. Create an empty directory named `logs`.  Set permissions and ownership on this file to allow the user executing CGI scripts to create, list, and delete files inside.
7. Create an empty directory named `database`.  Set permissions and ownership on this file to allow the user executing CGI scripts to create, list, and delete files inside.
8. Add execute permissions for `chat3.cgi`, `control3.cgi`, and `guard3.cgi`.
9. Set permissions and ownership on `lockfile.cgi` to allow the user executing CGI scripts to read and write to it.
   - The code correctly uses `flock`, but needs write permission to use `LOCK_EX`.

### Post-installation Tasks

To validate installation without possibly breaking anything, visit `chat3.cgi?action=closed` in your browser.  You should receive a polite message indicating that the chat room is closed.  You should not receive any Perl error messages, and nothing resembling code or techspeak should appear on the page.

If it all looks good, visit `control3.cgi`.  Log in with the default administrator password listed in `config.cgi`.  Follow the prompts to create a new primary administrator account, then delete the old administrator.

The chat should now operate properly.  Visit `index.php` and try it out.

### Troubleshooting Installation

 - Most error messages are passed through raw from Perl or PHP.  Nine times out of ten, it's file permissions or ownership.  Google the error and see what comes up.
 - Sometimes the blasted thing won't create the SQLite file inside the database directory.  Use the `sqlite3` to create an empty database, and set permissions and ownership as needed.  The next time `chat3.cgi` runs, the schema will be updated.

## Usage

### Core Concepts

### User Interface

#### For end-users

#### For Guards (Moderators)

#### For Administrators

## Inner Workings

### Theory of Operation

#### Historical Origins

#### "Bots & Proxies"

### Original Project Goals

See the TODO file that was removed during the commit that added this line.

