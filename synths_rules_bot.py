import praw
import datetime
import threading

from string import Template

MINUTES_TO_WARN = 1 # number of minutes before warning the user
MINUTES_TO_REMOVE = 5 # number of minutes before removing the post if the user has not commented
MIN_COMMENTERS_TO_KEEP = 5 # number of unique commenters to keep the post if the user has not commented

class SynthsRulesBot:
    def __init__(self):
        self.warning_template = Template(self.read_text_file('warning.txt'))
        self.removal_template = Template(self.read_text_file('removal.txt'))

        self.reddit = praw.Reddit('SynthRulesBot')
        subreddit = self.reddit.subreddit('SynthesizersSandbox')

        for submission in subreddit.new(limit=100):
            self.process_submission(submission)

    def process_submission(self, submission):
        if self.is_submission_actionable(submission):
            age = self.get_submission_age(submission)
            author_commented = self.did_author_comment(submission)
            target = None

            if age >= MINUTES_TO_REMOVE and not author_commented:
                target = self.remove_worker
            elif age >= MINUTES_TO_REMOVE and author_commented:
                target = self.cleanup_worker(submission)
            elif age >= MINUTES_TO_WARN and not author_commented:
                target = self.warning_worker

            if not target == None:
                thread = threading.Thread(target=target, args=(submission,))
                thread.start()

    def warning_worker(self, submission):
        if not self.find_mod_comment(submission):
            messaage = self.warning_template.substitute(
                author=submission.author.name, minutes=MINUTES_TO_REMOVE)
            
            mod_comment = submission.reply(messaage)
            mod_comment.mod.distinguish(sticky=True)
            mod_comment.mod.ignore_reports()
            
            self.log('Warned', submission)

    def remove_worker(self, submission):
        if self.get_unique_commenters_len() >= MIN_COMMENTERS_TO_KEEP:
            self.log('Submission appears engaging, will not remove', submission)
        else:
            submission.mod.remove(mod_note='Rule 5: Author did not comment')
            
            message = self.removal_template.substitute(
                author=submission.author.name, minutes=MINUTES_TO_REMOVE)
            submission.mod.send_removal_message(message)
            
            self.log('Removed', submission);

    def cleanup_worker(self, submission):
        mod_comment = self.find_mod_comment(submission)
        if not mod_comment == None and not mod_comment.removed:
            self.log('No longer actionable, cleaning up mod comments', submission)
            mod_comment.mod.remove(mod_note='Rule 5: Author commented')

    # 1. Not a self post
    # 2. Not locked
    # 3. Not distingushed 
    # 4. Not created by AutoModerator
    def is_submission_actionable(self, submission):
        return (not submission.is_self
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
        flattened_comments = submission.comments.list()

        for comment in flattened_comments:
            if comment.is_submitter:
                return True

        return False

    # Find the bot's moderation comment
    def find_mod_comment(self, submission):
        mod_commment = None

        for comment in submission.comments:
            if comment.author.name == 'SynthesizersBot' and comment.distinguished:
                mod_commment = comment
                break
        return mod_commment

    def get_unique_commenters_len(self, submission):
        unique = set()

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
        print(f'[{now}] {action}: \'{submission.title}\'')


if __name__ == '__main__':
    SynthsRulesBot()

def lambda_handler(event, context):
    SynthsRulesBot()