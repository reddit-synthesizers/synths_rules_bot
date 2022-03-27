import praw
import datetime
import os

from string import Template

DEFAULT_SUBREDDIT_NAME = 'synthesizers'

MINUTES_TO_WARN = 5  # number of minutes before warning the user
MINUTES_TO_REMOVE = 60  # number of minutes before removing the post if the user has not commented
MIN_COMMENTERS_TO_KEEP = 5  # number of unique commenters to keep the post if the user has not commented
OLDEST_SUBMISSION_AGE_TO_PROCESS = 90  # depending on how often the bot runs, this can optimize the # of API calls


class SynthsRulesBot:
    def __init__(self, subreddit_name=DEFAULT_SUBREDDIT_NAME):
        self.warning_template = Template(
            self.read_text_file('rule5-warning.txt'))
        self.removal_template = Template(
            self.read_text_file('rule5-removal.txt'))

        self.reddit = praw.Reddit('SynthRulesBot')
        subreddit = self.reddit.subreddit(subreddit_name)

        for submission in subreddit.new(limit=25):
            self.process_submission(submission)

    def process_submission(self, submission):
        if self.is_submission_actionable(submission):
            age = self.get_submission_age(submission)

            if age > OLDEST_SUBMISSION_AGE_TO_PROCESS:  # optimization
                return
                
            author_commented = self.did_author_comment(submission)

            if age >= MINUTES_TO_REMOVE and not author_commented:
                self.remove(submission)
            elif age >= MINUTES_TO_WARN and author_commented:
                self.cleanup(submission)
            elif age >= MINUTES_TO_WARN and not author_commented:
                self.warn(submission)

    def warn(self, submission):
        if not self.has_bot_comment(submission):
            messaage = self.warning_template.substitute(
                author=submission.author.name, minutes=MINUTES_TO_REMOVE)

            bot_comment = submission.reply(messaage)
            bot_comment.mod.distinguish(sticky=True)
            bot_comment.mod.ignore_reports()

            self.log('Warned', submission)

    def remove(self, submission):
        if self.get_unique_commenters_len(submission) >= MIN_COMMENTERS_TO_KEEP:
            self.log('Ignored', submission)
        else:
            submission.mod.remove(
                mod_note='Rule 5: OP did not comment, removed submission')

            message = self.removal_template.substitute(
                author=submission.author.name, minutes=MINUTES_TO_REMOVE)
            submission.mod.send_removal_message(message)

            self.log('Removed', submission)

    def cleanup(self, submission):
        bot_comments = self.find_bot_comments(submission)

        for comment in bot_comments:
            if not comment.removed:
                comment.mod.remove(
                    mod_note='Rule 5: OP commented, removed warning')
                self.log('Cleanup', submission)

    # 1. Not a self post
    # 2. Not locked
    # 3. Not distingushed
    # 4. Not created by AutoModerator
    def is_submission_actionable(self, submission):
        return (not submission.is_self
                and not submission.approved
                and not submission.locked
                and not submission.distinguished
                and not submission.author.name == 'AutoModerator')

    # returns submission age in minutes
    # why does PRAW use local time for UTC?
    def get_submission_age(self, submission):
        now = datetime.datetime.now()
        created = datetime.datetime.fromtimestamp(submission.created_utc)
        age = now - created
        return age.total_seconds() / 60

    # Did the OP leave a comment to the thread?
    def did_author_comment(self, submission):
        author_commented = False

        submission.comments.replace_more(limit=None)
        flattened_comments = submission.comments.list()

        for comment in flattened_comments:
            if comment.is_submitter:
                author_commented = True
                break

        return author_commented

    # Find the bot's moderation comment
    def find_bot_comments(self, submission):
        bot_comments = list()

        submission.comments.replace_more(limit=None)
        for comment in submission.comments:
            if comment.author.name == self.reddit.user.me():
                bot_comments.append(comment)

        return bot_comments

    def has_bot_comment(self, submission):
        return self.find_bot_comments(submission).__len__() > 0

    def get_unique_commenters_len(self, submission):
        unique = set()

        submission.comments.replace_more(limit=None)
        for comment in submission.comments:
            unique.add(comment.author)

        return unique.__len__()

    def read_text_file(self, filename):
        text = {}

        file = open(filename, 'r')
        text = file.read()
        file.close()

        return text

    def log(self, action, submission):
        now = datetime.datetime.now()
        name = type(self).__name__
        print(f'[{name}][{now}] {action}: \'{submission.title}\' ({submission.id})')


if __name__ == '__main__':
    SynthsRulesBot()


def lambda_handler(event, context):
    subreddit_name = os.environ['subreddit_name'] if 'subreddit_name' in os.environ else DEFAULT_SUBREDDIT_NAME
    SynthsRulesBot(subreddit_name=subreddit_name)
