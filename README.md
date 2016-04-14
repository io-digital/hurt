
# Hurt

> Various scripts to inflict damage on servers.

##### Inventory

* pain.py - HTTP load testing
  - Usage: `python pain/pain.py`
    + `--hits` number of requests 
    + `--workers` number of threads
    + `--url` host(name) to attack
    + `--timeout` request timeout in seconds

* tolerance.py - HTTP load testing (ncurses interface)
  - Usage: `python pain/tolerance.py`
    + `--tolerance` integer error limit
    + `--timeout` request timeout in seconds
    + `--url` host(name) to attack

* radial-fracture - RADIUS load testing
  - Usage: `node radial-fracture/radial-fracture.js example.com shared_secret 5000`
    + `process.argv[0]` host of radius server
    + `process.argv[1]` shared secret of radius server
    + `process.argv[2]` number of radius packets to send

##### Contributing

This repository accepts contributions for any language or runtime environment. However, please keep contributions in the realm of load/stress/penetration testing, or some other relevant thing not mentioned here. If you're unsure whether your contribution fits this project, please open an issue to discuss it!

Please fully document your script in the Inventory section of the README. Failure to do so will likely result in your contribution being rejected.

##### Legal

Use of this software indemnifies [us](https://io.co.za) against any liability for your actions.
