FPM
===

The files in this folder allows you to build a package for graphite-api with
[fpm](https://github.com/jordansissel/fpm). The resulting package is
completely isolated from your system-wide python packages. It's a packaged
virtual environment located at `/usr/share/python/graphite` that contains:

* Graphite-api with all its requirements and optional dependencies
* Gunicorn
* Config files (`/etc/graphite-api.yaml`, `/etc/default/graphite-api`)
* Creation of a `graphite` user on installation
* An init script in `/etc/init.d`

Prerequisites (to build a package)
----------------------------------

* FPM (`sudo gem install fpm`)
* `sudo apt-get install python-dev libffi-dev python-virtualenv`
* virtualenv-tools (either build it with fpm and install it or `sudo pip
  install virtualenv-tools`).

Building a package
------------------

./build-deb.sh

Deb packages are generated with fresh Debian and Ubuntu cloud instances and
the following cloud-init configuration:

```
#cloud-config
runcmd:
  - "wget https://raw.githubusercontent.com/brutasse/graphite-api/master/fpm/cloud-init.sh"
  - "sh cloud-init.sh"
```
