# ImmoScout Suchabo Discord Forwarder
Simple python script to forward emails received by ImmoScout Suchabo's to a discord channel via webhooks

The emails need to have a rule in gmail that automatically adds the 'immoscout' label. It checks every 10s for new mails and generates a discord embed with the image as an attachment. It also automatically sets the email as read.

See secret_example.py for the required configs. 

## Requirements
requests<br>
discord-webhook