# Installation

## Project Structure

The `bycon` project contains libraries (`/lib`), global configuration files
(`/config`), resource files (`/rsrc`) and data scheams (`/schemas`). All these
are distributed as part of the `bycon` package.

!!! warning "Highly Experimental"
    
    At this time the `bycon` configuration files are rather specific for
    the Progenetix use case. While in principle one can use the current code base
    to create a complete Beacon v2 setup this requires some customization, e.g.
    through editing the `/local/....yaml` configuration files as well as the 
    `/install.yaml` data.

Additionally to the library and associated files a complete `bycon`-base Beacon
server setup requires the installation of various endpoint apps contained in
`/beaconServer`. Progenetix also makes use of many server apps (e.g. for retrieving
supporting data such as collation statistics or genomic parameters) which are
now contained in the [`byconaut`](http://github.com/progenetix/byconaut/) project as `/services`.

##  `bycon` library install

In February 2023 `bycon` has been mad available as a Pypi package with standard
installation through `pip install bycon`. However, this installation will lack
the server components and is by itself only suitable for library utilization.

## Beacon Server Installation

### Requirements

An installation of a Beacon environment may involve following repositories:

* [`bycon`](https://github.com/progenetix/bycon/)
    - the core Beacon code for libraries and server API
* [`byconaut`](https://github.com/progenetix/byconaut/)
    - additional server functionality
    - utility scripts
    - example data
* [`progenetix-web`](https://github.com/progenetix/progenetix-web/)
    - the web front-end (React based)
    - represents the current Progenetix website w/ all its parts; can be used to 
    develop a trimmed-down version for specific use cases...

The project's Beacon deployment had been developed with some prerequisites:

#### MongoDB database instance


#### Webserver Setup (Apache)

We use a "classical" webserver setup with Apache but probably other options would
be fine...

Some configuration:

- a directory for executables (e.g. .../cgi-bin/) 
    * this has to be set as the default executable (CGI) directory
    * our Mac OS use: `/Library/WebServer/cgi-bin/`
```
# Configure the global CGI-BIN

ScriptAlias  /cgi      /Library/WebServer/cgi-bin
ScriptAlias  /cgi-bin  /Library/WebServer/cgi-bin

<Directory "/Library/WebServer/cgi-bin">
    AllowOverride None
    Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
    SetHandler cgi-script
    Require all granted
</Directory>
```
    * we also use a `/bycon` wrapper directory inside the CGI dir (for hosting the
      `beaconServer` and optionally `services` directories with their `....py`
      scripts)
    * we use a rewrite directive to the main beacon (& optional services) apps which
      handle then path deparsing and calling of individual apps:
```
# Allow (some) CGI-BIN scripts to be called with a short alias.

RewriteEngine On

RewriteRule     "^/?services/(.*)"     /cgi-bin/bycon/services/services.py/$1      [PT]
RewriteRule     "^/?beacon/(.*)"     /cgi-bin/bycon/beaconServer/beacon.py/$1      [PT]
```
- a server-writable temporary directory
    * our use: `/Library/WebServer/Documents/tmp/`
```
# Configure the global tmp

Alias  /tmp      /Library/WebServer/Documents/tmp

<Directory /Library/WebServer/Documents/tmp>
    Options Indexes FollowSymlinks
    AllowOverride All
    Require all granted
</Directory>
```
### Installation Procedure

The project root contains an `install.py` script to distribute the server scripts
into the webserver root. Necessary parameters have to be adjusted in the accompagnying
`install.yaml`.

!!! warning "Configuration adjustments"
    
    Many of the parameters in `bycon` are pre-defined in `bycon/config/....yaml`
    files which are installed into the `bycon` package in your Python `site-packages`
    tree. These configurations can be overwritten by providing modified copies
    in `your_script_directory/local/`.

#### Some configurations

##### `local/local_paths.yaml`

Here at minimum the paths for the webserver `tmp` has to be defined (path elements
as list items):

```
erver_tmp_dir_loc:
  - /
  - Library
  - WebServer
  - Documents
  - tmp

server_tmp_dir_web: /tmp
```

##### `local/beacon_defaults.yaml`

Please modify the data here, especially the defaults and the `eentity_defaults`
for the `info` entry type.

## Local stack installation 

The local developer mode installation removes the system `bycon`, compiles the
current code base (e.g. containing your modifications) and then runs the installer
script for the distribution of the server scripts. The following utility code
is provided with the `updev.sh` script (may change over time...):

```bash
pip3 uninstall bycon
rm -rf ./dist
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip install $BY
./install.py
../byconaut/install.py
```

The last step in the batch assumes that one has the `byconaut` project in a local
sister directory.

!!! note "Script dependencies"
    
    Many functions in `bycon` require the existence of local configuration files
    (e.g. for dataset definitions) in a `local` directory in the path of your
    calling scripts or CGIs.

## Loading data

We provide some data loading documentation and example data inside the
[`byconaut`](https://github.com/progenetix/byconaut/) package. This is evolving...

## Testing

The following tests are based on the existence of the `examplez` database.

### Command line test

Those tests can be run either from the local `bycon/bycon/beaconServer/` directory
or from the corresponding one in the web cgi directory, if installed.

```
./beacon.py --output json -d examplez --testMode true
./beacon.py --output json -d examplez --testMode true --requestEntityPathId g_variants
./beacon.py --output json -d examplez --testMode true --requestEntityPathId biosamples
./beacon.py --output json -d examplez --testMode true --requestEntityPathId individuals
./beacon.py --output json -d examplez --filters "UBERON:0000310"
./beacon.py --output json -d examplez --filters "pgx:TCGA-BRCA"
```


