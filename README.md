The [chickenpi project](https://github.com/Arghnews/chickenpi) has been running for years happily.

However one issue with it is that the raspberry pi for it lives in a wooden hut in the garden.
Wifi signal isn't strong enough to penetrate to the house where the router is.
The network connection for said rpi has always been via powerline through a long wire that runs from the house to the hut.

However, sometimes, particularly when there's a powercut, afterwards, the powerlines need resetting manually before they work again. Sometimes this occurs when the internet drops out too.

If these powercuts go unnoticed, then the raspberrypi in the coop may not work and may not be noticed.
That rpi will still open and close the doors, but can't be controlled from the internal website.
Also, very occasionally and more recently, the power supply to that rpi has been dropping voltage, down to ~ < 4.6V which means the rpi just can't turn on.
This also needs flagging and manually fixing by cranking up the voltage it outputs.

We can't have the raspberry pi itself tell us when its connection has failed, as of course, it can't speak to the home network.
So instead another rpi I have sitting around will run this little program, that will just constantly ping that raspberry pi, and if the connection drops for a sufficiently long time, will start sending sporadic emails to us to let us know.

TODO:
- Work out a better way of deploying code updates here to the raspberry doing the polling, rather than me copying the files across
- Only issue with something that kills the current running python process is let's say we were 5 hours into failure and going to send an email at 6 hours, then we update and kill it, we don't track state outside of a run. Then again as I type this scenario is so unlikely and the only consequence is knowing 6 hours later, will just do that
- Should increase time.sleep polling interval from 1 second
