Hurt is
=======

Hurt is purgatory for servers. Here they are purified before they go.

Hurt is a developer playground. You get the chance to get back at them.

Hurt is a collection of scripts in any language inflicting damage on any server running any protocol on any port.

Hurt is not
===========

A repo of DDoS scripts. Go write your own script kid.

Inventory
=========

1. pain.py
----------

A script to inflict HTTP pain. The following applies:

`python pain.py`

 - `--hits` default=2000 Number of requests
 - `--workers` default=500 Number of workers
 - `--url` The URL to punish
 - `--timeout` default=5

2. radial-fracture
------------------

send packets to a given radius server

`node radial-fracture/radial-fracture.js`

note that radial-fracture uses positional arguments, not named arguments:

- **argv[0]** default=undefined, type=string, host of radius server
- **argv[1]** default=undefined, type=string, shared secret of radius server
- **argv[2]** default=undefined, type=integer, number of radius packets to send

Contribution
============

We want to build up a library that we may use to stress test server setups and apps. If you simply want to use it as a place to write some new language code or to play please do so.

No language is specified but please keep it to one script which may be fired using one command. Also add it to the inventory in this readme. If you come up with a reason for this contribution rule to be invalid, change it by pull request. 
