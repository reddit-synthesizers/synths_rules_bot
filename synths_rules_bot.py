import praw
import datetime
import os

from string import Template

DEFAULT_SUBREDDIT_NAME = 'synthesizers'

MINUTES_TO_WARN = 5  # number of minutes before warning the user
MINUTES_TO_REMOVE = 60  # number of minutes before removing the post if the user has not commented
MIN_UNIQUE_COMMENTERS_TO_KEEP = 5  # number of unique commenters to keep the post if the user has not commented
OLDEST_SUBMISSION_AGE_TO_PROCESS = 90  # depending on how often the bot runs, this can optimize the # of API calls
MAX_SUBMISSIONS_TO_PROCESS = 25  # tweak depending on the subreddit's volume and how often the bot runs


class SynthsRulesBot:
    def __init__(self, subreddit_name=DEFAULT_SUBREDDIT_NAME, dry_run=False):
        self.dry_run = dry_run

        self.reddit = praw.Reddit('SynthRulesBot')
        subreddit = self.reddit.subreddit(subreddit_name)

        self.warning_template = Template(
            self.read_text_file('rule5-warning.txt'))

        self.removal_template = Template(
            self.read_text_file('rule5-removal.txt'))

        for submission in subreddit.new(limit=MAX_SUBMISSIONS_TO_PROCESS):
            if self.submission_is_actionable(submission):
                self.process_submission(submission)

    def process_submission(self, submission):
        age = self.get_submission_age(submission)

        if age <= OLDEST_SUBMISSION_AGE_TO_PROCESS:
            author_commented = self.did_author_comment(submission)
            was_warned = self.was_warned(submission)

            if age >= MINUTES_TO_REMOVE and not author_commented:
                self.remove(submission)
            elif age >= MINUTES_TO_WARN and author_commented and was_warned:
                self.cleanup(submission)
            elif age >= MINUTES_TO_WARN and not author_commented and not was_warned:
                self.warn(submission)

    def remove(self, submission):
        unique_commentors = self.get_unique_commenters_len(submission)

        if unique_commentors < MIN_UNIQUE_COMMENTERS_TO_KEEP:
            if not self.dry_run:
                submission.mod.remove(
                    spam=False, mod_note='Rule 5: OP did not comment, removed submission')

                message = self.removal_template.substitute(
                    author=submission.author.name, minutes=MINUTES_TO_REMOVE)
                submission.mod.send_removal_message(message)

            self.log('Removed', submission)
        else:
            submission.mod.approve()
            self.log('Ignored', submission)

    def cleanup(self, submission):
        if not self.dry_run:
            self.remove_warning_comment(
                submission, 'Rule 5: OP commented, removed warning')

        self.log('Cleanup', submission)

    def warn(self, submission):
        if not self.dry_run:
            messaage = self.warning_template.substitute(
                author=submission.author.name, minutes=MINUTES_TO_REMOVE)

            bot_comment = submission.reply(messaage)
            bot_comment.mod.distinguish(sticky=True)
            bot_comment.mod.ignore_reports()

        self.log('Warned', submission)

    # 1. Not a self post
    # 2. Not locked
    # 3. Not distingushed
    # 4. Not created by AutoModerator
    def submission_is_actionable(self, submission):
        return (not submission.is_self
                and not submission.approved
                and not submission.locked
                and not submission.distinguished
                and not submission.author.name == 'AutoModerator')

    # Returns submission age in minutes
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

    def was_warned(self, submission):
        return self.find_warning_comment(submission) is not None

    def find_warning_comment(self, submission):
        warning_comment = None

        if len(submission.comments) > 0:
            first_comment = submission.comments[0]

            if (first_comment.author.name == self.reddit.user.me() and first_comment.stickied):
                message = self.warning_template.substitute(
                    author=submission.author.name, minutes=MINUTES_TO_REMOVE)

                if first_comment.body.startswith(message[:10]):  # avoid removing our other bot's warnings
                    warning_comment = first_comment

        return warning_comment

    def remove_warning_comment(self, submission, mod_note=''):
        warning_comment = self.find_warning_comment(submission)
        if warning_comment is not None:
            warning_comment.mod.remove(spam=False, mod_note=mod_note)

    def get_unique_commenters_len(self, submission):
        unique = set()

        submission.comments.replace_more(limit=None)
        for comment in submission.comments:
            unique.add(comment.author)

        return len(unique)

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


def lambda_handler(event=None, context=None):
    subreddit_name = os.environ['subreddit_name'] if 'subreddit_name' in os.environ else DEFAULT_SUBREDDIT_NAME
    dry_run = os.environ['dry_run'] == 'True' if 'dry_run' in os.environ else False
    SynthsRulesBot(subreddit_name=subreddit_name, dry_run=dry_run)


if __name__ == '__main__':
    lambda_handler()
