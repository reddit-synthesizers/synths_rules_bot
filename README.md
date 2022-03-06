# r/synthesizers rules bot

This bot enforces r/synthesizers Rule 5: 

```
Leave a Comment on Link/Photo/Video Posts

Link, photo, and video posts must include a meaningful comment by the OP. 
“Here is a track I made” or "look at my new synth" is not sufficient since the point is 
to encourage discussion. Posts lacking a comment will be removed at the moderators discretion.
```

By default, it will monitor the (up to) 100 newest submissions for link submissions where the OP did not leave a meaningful comment. 

After *N* minutes bot will leave a sticky comment warning the OP to post a comment.

After *M* minutes, if the OP has not posted a comment, or if the bot does not rule the submission is a engaging (determined by the number of unique commenters), the submission will be removed.

# Installation

1. The only Python requirement is [PRAW](https://praw.readthedocs.io/en/stable/). Read the [installation](https://praw.readthedocs.io/en/stable/getting_started/installation.html) docs there for instructions on how to install.
2. You'll need to create a personal use script on [Reddit's app portal](https://ssl.reddit.com/prefs/apps/). The developer should be a mod on the subreddit that the bot will monitor.
3. Modify praw.ini with your client id and client secret (from Reddit's app portal) along with the developer's Reddit username and password.
4. The script is stateless and does its work in one pass. It's intended to run periodically via cron or AWS Lambda, etc.
