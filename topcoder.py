from urllib2 import urlopen
from lxml import objectify
import numpy as np
import matplotlib.pyplot as plt
import os


class Match(object):

    def __init__(self, rating_history, match_details):
        self.round_id = rating_history.round_id
        self.short_name = rating_history.short_name
        self.date = rating_history.date
        self.old_rating = rating_history.old_rating
        self.new_rating = rating_history.new_rating
        self.volatility = rating_history.volatility
        self.rank = rating_history.rank
        self.percentile = rating_history.percentile

        fields = ['division_placed', 'challenge_points', 'final_points', 'division',
            'problems_presented', 'problems_submitted', 'problems_correct']

        problem_details = ['level_%s_problem_id', 'level_%s_submission_points',
            'level_%s_final_points', 'level_%s_status', 'level_%s_time_elapsed',
            'level_%s_placed', 'level_%s_language']

        for field in fields:
            setattr(self, field, getattr(match_details, field))

        for level in ('one', 'two', 'three'):
            for problem in problem_details:
                param = problem % (level)
                setattr(self, param, getattr(match_details, param))

        self.total_participants = 0
        self.level_one_correct_submissions = 0
        self.level_one_average_score = 0

        self.level_two_correct_submissions = 0
        self.level_two_average_score = 0

        self.level_three_correct_submissions = 0
        self.level_three_average_score = 0

        self.getStats()

    def getStats(self):
        with file('data/%d.xml' % (self.round_id), "r") as f:
            round_data = objectify.fromstring(f.read())
            l1, l2, l3 = [], [], []
            self.total_participants = 0
            for coder in round_data.iterchildren():
                if coder.division == self.division:
                    l1.append(coder.level_one_final_points)
                    l2.append(coder.level_two_final_points)
                    l3.append(coder.level_three_final_points)

                    self.total_participants += 1

            l1 = filter(lambda x: x, l1)
            l2 = filter(lambda x: x, l2)
            l3 = filter(lambda x: x, l3)

            self.level_one_correct_submissions = len(l1)
            self.level_two_correct_submissions = len(l2)
            self.level_three_correct_submissions = len(l3)

            if l1:
                self.level_one_average_score = sum(l1) * 1.0 / len(l1)
            if l2:
                self.level_two_average_score = sum(l2) * 1.0 / len(l2)
            if l3:
                self.level_three_average_score = sum(l3) * 1.0 / len(l3)


class TopCoder(object):
    """
    Fetches all the matches a coder has participated in.
    """

    BASE_URL = "http://community.topcoder.com/tc?module=BasicData&"

    def __init__(self, handle):
        """
        Uncomment the "getAlgoFeeds" and "getCoders" methods to
        fetch all the data from topcoder website. It creates a copy
        on the disk before processing
        """

        #self.getAlgoFeeds()
        #self.getCoders()
        self.matches = []
        self.handle = handle
        self.coder_id = self.getCoderID()
        self.getCoderStats()
        self.matches.sort(lambda x, y: x.date < y.date)
        self.displayStats()

    def getCoderStats(self):
        api_endpoint = "%sc=dd_rating_history&cr=%d" % (TopCoder.BASE_URL, self.coder_id)
        content = urlopen(api_endpoint).read()
        rating_history = objectify.fromstring(content)
        for match_info in rating_history.iterchildren():
            coder_data = self.getRoundData(match_info.round_id)
            self.matches.append(Match(match_info, coder_data))

    def getCoderID(self):
        coders = ""
        with file('data/coders.xml', "r") as f:
            coders = f.read()
            f.close()

        coders = objectify.fromstring(coders)
        for coder in coders.iterchildren():
            if coder.handle == self.handle:
                return coder.coder_id

    def getAlgoFeeds(self):
        api_endpoint = "%sc=dd_round_list" % (TopCoder.BASE_URL)
        rounds = urlopen(api_endpoint).read()
        rounds = objectify.fromstring(rounds)
        file_list = os.listdir("data")

        for rnd in rounds.iterchildren():
            if str(rnd.round_id) + '.xml' in file_list:
                continue
            try:
                api_endpoint = "%sc=dd_round_results&rd=%d" % (TopCoder.BASE_URL,
                    rnd.round_id)
                match_data = urlopen(api_endpoint).read()
                with file('data/%d.xml' % rnd.round_id, "w") as f:
                    f.write(match_data)
                    f.close()
            except:
                pass

    def getCoders(self):
        api_endpoint = "%sc=dd_coder_list" % (TopCoder.BASE_URL)
        coders = urlopen(api_endpoint).read()
        with file('data/coders.xml', "w") as f:
            f.write(coders)
            f.close()

    def getRoundData(self, round_id):
        with file('data/%d.xml' % (round_id), "r") as f:
            round_data = objectify.fromstring(f.read())
            for coder in round_data.iterchildren():
                if coder.coder_id == self.coder_id:
                    return coder

    def getCumulativeCount(self, scores):
        cumulative = map(lambda x: int(x != 0), scores)
        for idx, score in enumerate(cumulative):
            if idx == 0:
                continue
            cumulative[idx] += cumulative[idx - 1]
        return cumulative

    def displayStats(self):
        level_one_scores = [int(x.level_one_final_points) for x in self.matches]
        level_one_averages = [int(x.level_one_average_score) for x in self.matches]
        level_two_scores = [int(x.level_two_final_points) for x in self.matches]
        level_two_averages = [int(x.level_two_average_score) for x in self.matches]
        x = np.arange(0, len(level_one_averages), 1)

        level_one_cumulative = self.getCumulativeCount(level_one_scores)
        level_two_cumulative = self.getCumulativeCount(level_two_scores)

        plt.plot(x, level_one_cumulative, 'ro', x, level_two_cumulative, 'g^')
        plt.show()


def main():
    TopCoder("krishbharadwaj")


if __name__ == '__main__':
    main()
