# iss_reboost_detector

Source code for the bot running at https://twitter.com/iss_reboosts

I have this running as a cron job. This script gets called every hour (once per hour seems like the right balance to get fast updates, without over-spamming Celestrak).

This also gets piped to a log file for all the print statements to keep track of any unexpected behaviors.

The twitter_creds file is censored; the software as-deployed has the Twitter credentials for the @iss_reboosts filled in, but of course I don't want those to be deployed to Github, so it has placeholders.

More than happy to take requests (either in pull-request form or by messaging me, or otherwise). If you find a bug or a way the logic can be improved, I'd love to hear it! This is kind of just something I've thrown together and could definitely be improved, but for now it seems to get the job done.
