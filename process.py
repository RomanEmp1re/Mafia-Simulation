from roles import Player, MafiaPlayer, DonPlayer, SeriffPlayer
import random
import pandas as pd

class Table:
    roles = [MafiaPlayer] * 2 + [DonPlayer] + [Player] * 6 + [SeriffPlayer]
    random.shuffle(roles)
    def __init__(self):
        self.players = pd.Series(
            index=range(1, 11),
            data=[None]*10
        )
        for i in self.players.index:
            self.players[i] = self.roles[i - 1](i)
        self.info_table = pd.DataFrame(
            index=range(1, 11),
            data = {
                'color': map(lambda x : -1 if isinstance(x, MafiaPlayer) else 1, self.players),
                'seriff': map(lambda x : 1 if isinstance(x, SeriffPlayer) else -1, self.players),
                'alive': [True] * 10
            }
        )
        for i in self.players:
            if isinstance(i, MafiaPlayer):
                i.knowledge['color'] = self.info_table['color']

    def alive_players(self):
        return [p for p in self.players if p.alive]

    def alive_players_id(self):
        return [p.id for p in self.players if p.alive]

    def mafia_players(self, alive_flag):
        return [
            p for p in self.alive_players()
            if type(p) in (MafiaPlayer, DonPlayer)
            and (alive_flag or p.alive)]

    def mafia_players_id(self, alive_flag):
        return [
            p.id for p in self.alive_players()
            if type (p) in (MafiaPlayer, DonPlayer)
            and (alive_flag or p.alive)
        ]

    def citizen_players(self, alive_flag):
        return [
            p for p in self.alive_players()
            if type(p) not in [MafiaPlayer, DonPlayer]
            and (alive_flag or p.alive)
        ]

    def citizen_players_id(self, alive_flag):
        return [
            p.id for p in self.alive_players()
            if type(p) not in [MafiaPlayer, DonPlayer]
            and (alive_flag or p.alive)
        ]

    def don(self, alive_flag):
        return [
            p for p in self.alive_players() if isinstance(p, DonPlayer)
            and (alive_flag or p.alive)][0]

    def don_id(self, alive_flag):
        return [p.id for p in self.alive_players() if isinstance(p, DonPlayer)
                and (alive_flag or p.alive)][0]

    def seriff(self, alive_flag):
        return [p for p in self.alive_players() if isinstance(p, SeriffPlayer)
                and (alive_flag or p.alive)][0]

    def seriff_id(self, alive_flag):
        return [p.id for p in self.alive_players() if isinstance(p, SeriffPlayer)
                and (alive_flag or p.alive)][0]


class Election:
    '''
    Класс для голосования
    '''
    def __init__(self, candidates, re_election=False):
        self.candidates = candidates
        self.candidates_id = (c.id for c in candidates)
        self.re_election = re_election
        self.election_list = pd.DataFrame(
            index=self.candidates_id,
            columns=[
                'votes_for',
                'votes_recieved',
                'voted_by'
            ]
        )
        self.election_list['votes_for'] = 0
        self.election_list['votes_recieved'] = 0
        self.election_list['players_voted'] = []
        self.election_list.dtypes = {
            'votes_for': 'Int64',
            'votes_recieved' : 'Int64'
        }
        self.election_log = ''

    def log(self, event, players=None, victim=None):
        if self.election_log != '':
            self.election_log += '\n'
        if players:
            players = ' '.join(str(p).ljust(2) for p in players)
        if victim:
            victim = str(victim)
        match event:
            case 'declare':
                self.election_log += (
                    f'Объявлено голосование между игроками {players}')
            case 'vote':
                self.election_log += (
                    f'  За игрока {victim.ljust(2)} проголосовали игроки {players}')
            case 'leader':
                self.election_log += (
                    f'  Лидером голосования стал игрок {victim}'
                )
            case 'share':
                self.election_log += (
                    f'  Голоса разделились поровну между игроками {players}'
                )
            case 'mass':
                self.election_log += (
                    f'  Ставится вопрос о подъеме игроков {players}'
                )
            case 'lift':
                self.election_log += (
                    f'  Было принято решение о подъеме игроков {players}'
                )
            case 'leave':
                self.election_log += (
                    f'  Было принято решение оставить игроков {players}'
                )
            case 'reelection':
                self.election_log += (
                    f'Объявлено переголосование между игроками {players}'
                )

    def election_process(self, candidates):
        if self.re_election:
            self.log(event='reelection', candidates=self.candidates)
        else:
            self.log(event='declare', candidates=self.candidates)
        for p in self.candidates:
            p.vote(p.target_for_vote(self.candidates_id), self.election_list)
        for p in self.election_list.query('votes_recieved > 0').iterrows():
            self.log(event='vote', players=p['voted_by'])
        max_votes = self.election_list['votes_recieved'].max()
        leaders_id = self.election_list.query('votes_recieved == @max_votes')
        if len(leaders_id) == 1:
            victim = leaders_id[0]
            self.table.players[victim].alive = False
            self.log('leader', victim=victim)
            return leaders_id, True # True означает, что голосование проведено 
        else:
            self.log('share', players=leaders_id)
            if self.re_election:
                self.log('mass', players=leaders_id)
                if random.random() > 0.5:
                    for l in leaders_id:
                        l.alive = False
                        self.log('lift', players=leaders_id)
                    return leaders_id, True
                else:
                    self.log('leave', players=leaders_id)
                return [], True
            else:
                return leaders_id, False


class Game:
    def __init__(self):
        self.table = Table()
        self.elections = {}
        self.day = 0
        self.election_id = 0

    @property
    def day_str(self):
        return f'День {str(self.day)}'

    @property
    def election_num_str(self):
        return f'голосование {str(self.election)}'

    @property
    def day_election(self):
        return self.day_str + ' ' + self.election_num_str

    def election(self, re_election=False):
        self.election_id += 1
        self.elections[self.day_election] = Election(table=self.table, re_election=re_election)
        result = self.voting_process()
        if not result[1]:
            result = self.voting_process(candidates=result[0], second_round=True)
        if len(result[0]) == 1:
            print('В результате голосования выбывает игрок ' + str(result[0][0]))
        elif len(result[0]) == 0:
            print('В результате голосования никто не покидает стол')
        else:
            print('В результате голосования выбывают игроки: ' + ','.join(result[0]))
        self.actualize_info('alive')

    def night_shooting(self):
        for p in self.table.mafia_players(alive_flag=True):
            if p.shot_assigner:
                victim = p.shot(self.table.players[p.target_for_shot()])
                self.table.info_table.loc[victim.id, 'alive'] = False
                print('Этой ночтю был застрелян игрок ' + str(victim))
        return victim.id

    def seriff_check(self):
        self.seriff.check(self.seriff.pick_verify())

    def don_check(self):
        self.don.check(self.don.pick_verify())

    def morning(self):
        self.actualize_info('alive')

    def actualize_info(self, param):
        for p in self.table.players:
            p.knowledge[param] = self.table.info_table[param]


if __name__=='__main__':
    print('Добро пожаловать в интеллектуально-психологическую игру "Мафия"')
    g = Game()
    print(g.table.players)
    g.day_voting()
    pass
'''
Проблема при голосовании
Проголосовавший игрок попадает в election_list с votes_recieved = Nan
Далее, так как он там, то он становится целью для следующих голосований
Решение - передавать в target_for_vote только кандидатов
'''