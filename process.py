from roles import Citizen, Mafia, Don, Sheriff
import random
import pandas as pd


ALIVE = 1
BLACK = -1
RED = 1
UNKNOWN = 0
YES = 1
NO = - 1

'''
class Election:
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
                '''


class Game:
    roles = [Mafia] * 2 + [Don] + [Citizen] * 6 + [Sheriff]
    def __init__(self):
        self.roles_random = self.roles.copy()
        random.shuffle(self.roles_random)
        self.game_log = 'Добро пожаловать в интеллектуально'\
            '-психологическую игру Мафия!'
        self.players = pd.Series(
            index=range(1, 11),
            data=None
        ).astype('object')
        for i in self.players.index:
            self.players[i] = self.roles_random[i - 1](i)
        self.update_table()
        self.log('roles')
        for i in self.players:
            if isinstance(i, Mafia):
                i.knowledge['color'] = self.table['color']
        self.log('mafia_talk')
        self.log('sheriff_sign')

    def update_table(self):
        self.table = pd.DataFrame(
            index=range(1, 11),
            data = {
                'color': map(lambda x : BLACK if isinstance(x, Mafia) else RED, self.players),
                'seriff': map(lambda x : YES if isinstance(x, Sheriff) else NO, self.players),
                'role': map(lambda x : x.role, self.players),
                'alive': map(lambda x : YES if x.alive else NO, self.players)
            }
        )


    def get_players(self, color=None, role=None, alive=None, type_result='obj'):
        result = self.players.copy()
        if color is not None:
            result = result[self.table['color']==color]
        if role is not None:
            result = result[self.table['role']==role]
        if alive is not None:
            result = result[self.table['alive']==alive]
        match type_result:
            case 'obj':
                return result
            case 'int':
                return [p.id for p in result]
            case 'str':
                return ' '.join([str(p.id).ljust(2) for p in result])

    # ведение лога игры
    def log(self, event, object1=None, object2=None):
        self.game_log += '\n'
        match event:
            case 'roles':
                self.game_log += f'Карты розданы, в игре у иргоков следующие роли:\n{self.table}'
            case 'mafia_talk':
                self.game_log += 'Мафия знакомится, черная команда : ' + \
                    self.get_players(color=-1, type_result='str') +\
                    ', дон игры - ' + self.get_players(role='Дон', type_result='str')
            case 'sheriff_sign':
                self.game_log += 'Шериф игры - ' + self.get_players(role='Шериф',
                    type_result='str')
                    

    # ночной отстрел
    def hunt(self):
        pass

    # проверка дона
    def don_check(self):
        pass

    # проверка шерифа
    def sheriff_cjeck(self):
        pass

    # актуализация знаний жителей
    def update_knowledge(self):
        pass

    # голосование
    def election(self, re_election=False):
        pass

    # проверка условия победы
    def check_win(self):
        pass
    
    def start_game(self):
        for i in range(20):
            self.log(event='night') # ночь
            self.hunt()
            match self.check_win():
                case 1:
                    self.log(event='city won')
                    break
                case -1:
                    self.log(event='mafia won')
            self.don_check()
            self.sheriff_check()
            self.update_knowledge()
            e = self.election()
            if len(e) > 1:
                self.election(re_election=True)
            self.update_knowledge()
            match self.check_win():
                case 1:
                    self.log(event='city won')
                    break
                case -1:
                    self.log(event='mafia won')

if __name__=='__main__':
    g1 = Game()
    print(g1.players)
    g1.players[4].alive = False
    g1.players[5].alive = False
    g1.players[6].alive = False
    g1.players[7].alive = False
    g1.update_table()
    print(g1.table)
    print(g1.get_players(color=-1, alive=1, type_result='str'))
    
