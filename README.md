I have a raspberry pi with an LED light plugged into one of its USB ports. I am able to turn the power off to the USB port with
sudo uhubctl -l 1-1 -p 2 -a off and on with sudo uhubctl -l 1-1 -p 2 -a on.

This application should have two parts:

1. Something that lives on the raspberry pi and monitors some remote state shich is uses to toggle the USB power on an off
2. Something that is exposed to the internet that let's us change that remote state.

I would like the web application to know the current state, and I would like the response of the light to be as instant as possible.
