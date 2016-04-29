# Tolerance is a tool to establish the health of HTTP servers and the networking to them.

Essentially what Tolerance does is incrementally request more and more 
simultaneous connections from the specified host until it breaks. Most 
hosts will break. This is not a test you're trying to pass, you simply
 want to better understand your systems.

 
We developed Tolerance while building systems for literal stadiums full
of people, where both our servers and the connectivity in the stadium
had to be perfect.
 
There are two reasons to run tolerance. 

1. **To Test Your HTTP Server**. Tolerance is a very effective way to
see how well your host holds up. Protip: Compare a page that makes db 
calls against a straight nginx file asset.

2. **To Test Your Connectivity**. First know how much abuse a server 
can take. Install tolerance somewhere with solid hardware and fat 
pipes, then run a test against your host for a benchmark. 
 
Now you can use Tolerance inside your test-network environment to 
establish that network's health. Also check various other connections 
for benchmarks (eg. GSM, Home DSL/Fibre etc).
 
 
# Warning
While Tolerance usually won't do any permanent damage, it is possible
that it might break a host in a way that requires a reboot etc. You 
are certainly likely to cause some degradation in service, if not DDOS 
it completely for a few seconds.
