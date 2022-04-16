# r/synthesizers rules bot

This bot enforces r/synthesizers Rule 5: 

```
Leave a Comment on Link/Photo/Video Posts

Link, photo, and video posts must include a meaningful comment by the OP. 
“Here is a track I made” or "look at my new synth" is not sufficient since the point is 
to encourage discussion. Posts lacking a comment will be removed at the moderators discretion.
```

By default, it will monitor the (up to) 25 newest submissions for link submissions where the OP did not leave a meaningful comment. 

After *N* minutes bot will leave a sticky comment warning the OP to post a comment.

After *M* minutes, if the OP has not posted a comment, or if the bot does not rule the submission is a engaging (determined by the number of unique commenters), the submission will be removed.

# Installation

1. The only Python requirement is [PRAW](https://praw.readthedocs.io/en/stable/). Read the [installation](https://praw.readthedocs.io/en/stable/getting_started/installation.html) docs there for instructions on how to install.
2. You'll need to create a personal use script on [Reddit's app portal](https://ssl.reddit.com/prefs/apps/). The developer should be a mod on the subreddit that the bot will monitor.
3. Modify praw.ini with your client id and client secret (from Reddit's app portal) along with the developer's Reddit username and password.

# Notes

This bot was designed to run periodically, either via a cron job or in a serverless environment. Many of the design decisions going into it (statelessness first and foremost) were driven by the need to run it as a Lambda on the AWS free tier. For a medium sized sub, the bot runs on r/synthesizers in under 2 seconds. When run every minute, this is well below the AWS free tier limit of 400K GB-seconds / 1MM requests per month. In fact, all three r/synthesizers bots use only about 10% of the free tier Lambda budget per month. The bot uses an average of 5 Reddit API calls per invocation, putting safely under the Reddit API limit of [60 requests per minute](https://github.com/reddit-archive/reddit/wiki/API#rules). For larger subs, configured with a higher value for `MAX_SUBMISSIONS_TO_PROCESS` YMMV.