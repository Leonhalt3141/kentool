# -*- coding: utf-8 -*-

import datetime
import pytz
import slack
from github import Github

from .meta_info import *


base_message = """
Lines edited on {0}
*Total: {1}, Additions: {2}, Deletions: {3}*
"""


class GitHubReport(object):
    def __init__(self):
        self.g = Github(GITHUB_TOKEN)
        self.slack_client = slack.WebClient(token=SLACK_API_TOKEN)

    def get_stats(self, repo_name):
        """

        :param repo_name:
        :type repo_name: str
        :return:
        """

        repo_path = GITHUB_ACCOUNT + "/" + repo_name
        repo = self.g.get_repo(repo_path)

        stats = {'total': 0, 'additions': 0, 'deletions': 0}

        commits = repo.get_commits()

        for commit in commits:
            data = commit.raw_data

            today = datetime.datetime.now(datetime.timezone.utc)

            date_range = [today.replace(hour=0, minute=0, second=0), today - datetime.timedelta(days=1)]
            committed_date = datetime.datetime.strptime(data['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ'
                                                        ).replace(tzinfo=pytz.UTC)

            if data['commit']['author']['name'] in AUTHORS and date_range[0] <= committed_date <= date_range[1]:
                stats['total'] += data['stats']['total']
                stats['additions'] += data['stats']['additions']
                stats['deletions'] += data['stats']['deletions']
            else:
                pass

        if stats['total'] > 0:
            return stats
        else:
            return None

    def summarise_status(self):
        summary = {}

        for repo_name in repo_names:
            stats = self.get_stats(repo_name)
            if stats is not None:
                summary[GITHUB_ACCOUNT + '/' + repo_name] = stats

        return summary

    @staticmethod
    def create_slack_message(summary):
        """

        :param summary: dict
        :return:
        """
        today = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone('US/Pacific'))

        if summary is not None:
            total = sum([summary[repo]['total'] for repo in summary.keys()])
            additions = sum([summary[repo]['additions'] for repo in summary.keys()])
            deletions = sum([summary[repo]['deletions'] for repo in summary.keys()])

            message = base_message.format(today.strftime('%Y/%m/%d (US/Pacific)'), total, additions, deletions)

            for repo in summary.keys():
                text = "\t`{0}` Total: {1}, Additions: {2}, Deletions: {3}\n".format(repo,
                                                                                     summary[repo]['total'],
                                                                                     summary[repo]['additions'],
                                                                                     summary[repo]['deletions'])
                message += text
        else:
            message = base_message + "\nNo edited lines"

        return message

    def send_to_slack(self, message):
        response = self.slack_client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        assert response['ok']

    def send_summary(self):
        summary = self.summarise_status()
        message = self.create_slack_message(summary)
        self.send_to_slack(message)


def send_daily_summary():
    report = GitHubReport()
    report.send_summary()
