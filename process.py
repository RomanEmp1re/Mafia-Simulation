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
        self.game_log = ''

    def log(self, event, players=None, victim=None):
        if self.game_log != '':
            self.game_log += '\n'
        if players:
            players = ' '.join(str(p).ljust(2) for p in players)
        if victim:
            victim = str(victim)
        match event:

    def election_process(self, candidates):
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
        for i in self.get_players(color=-1):
            i.knowledge['color'] = self.table['color']
            print(self.get_players(color=-1, type_result='int'))
            i.knowledge.loc[list(i.get_players(color=-1)), 'sheriff'] = -1
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
    def log(self, event, **kwargs):
        self.game_log += '\n'
        match event:
            case 'roles':
                self.game_log += f'Карты розданы, в игре у игроков следующие роли:\n{self.table}'
            case 'mafia_talk':
                self.game_log += (
                    'Мафия знакомится, черная команда: ' +
                    self.get_players(color=-1, type_result='str') +
                    ', дон игры — ' + self.get_players(role='Дон', type_result='str')
                )
            case 'sheriff_sign':
                self.game_log += (
                    'Шериф игры — ' +
                    self.get_players(role='Шериф', type_result='str')
                )
            case 'hunt':
                victim = kwargs['victim']
                self.game_log += f'Этой ночью был убит игрок {victim}'
            # === ГОЛОСОВАНИЕ ===
            case 'declare_election':
                players = ' '.join(str(i) for i in kwargs['players'])
                self.game_log += f'\nОбъявлено голосование между игроками {players}'
            case 'vote':
                players = ' '.join([str(p) for p in kwargs['players']])
                victim = str(kwargs['victim'])
                self.game_log += f'\n  За игрока {victim} проголосовали игроки {players}'
            case 'leader':
                victim = str(kwargs['victim'])
                self.game_log += f'\n  Лидером голосования стал игрок {victim}'
            case 'share':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'\n  Голоса разделились поровну между игроками {players}'
            case 'mass':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'\n  Ставится вопрос о подъеме игроков {players}'
            case 'lift':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'\n  Было принято решение о подъеме игроков {players}'
            case 'leave':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'\n  Было принято решение оставить игроков {players}'
            case 'reelection':
                players = ' '.join(str(p) for p in kwargs['candidates'])
                self.game_log += f'\nОбъявлено переголосование между игроками {players}'  

    # ночной отстрел
    def hunt(self):
        for m in self.get_players(color=-1, alive=1):
            if m.shot_assigner:
                target = m.shot()
                self.players[target].alive = False
                self.log(event='hunt', victim=target)
                self.update_table()
                break

    # проверка дона
    def don_check(self):
        pass

    # проверка шерифа
    def sheriff_cjeck(self):
        pass

    # актуализация знаний жителей
    def update_knowledge(self):
        for p in self.players:
            p.knowledge['alive'] = self.table['alive']

    # голосование
    def election(self, candidates_id:list[int], re_election=False):
        election_list = pd.DataFrame(
            index=candidates_id, data={'voted_by': None, 'votes_recieved':0})
        election_list['voted_by'].astype('object')
        election_list['voted_by'] = [[] for _ in range(len(candidates_id))]
        if re_election:
            self.log(event='reelection', candidates=candidates_id)
        else:
            self.log(event='declare_election', players=candidates_id)
        voters = self.get_players(alive=1)
        for p in voters:
            target = p.vote(candidates_id)
            election_list.loc[target, 'voted_by'].append(p.id)
            election_list.loc[target, 'votes_recieved'] += 1
        for p in election_list.query('votes_recieved > 0').iterrows():
            self.log(event='vote', players=p[1], victim=p[0])
        max_votes = election_list['votes_recieved'].max()
        leaders_id = election_list.query('votes_recieved == @max_votes').index.to_list()
        if len(leaders_id) == 1: # когда был выбран один игрок
            victim = leaders_id[0]
            self.players[victim].alive = False
            self.log('leader', victim=victim)
            return [victim], True # True означает, что голосование проведено 
        else: # выбрано несколько игроков на голосовании
            self.log('share', players=leaders_id)
            if re_election:
                self.log('mass', players=leaders_id)
                if random.random() > 0.5: # пока заглушка - поднять или оставить 50/50
                    for l in leaders_id:
                        self.players[leaders_id].alive = False
                        self.log('lift', players=leaders_id)
                    return leaders_id, True
                else:
                    self.log('leave', players=leaders_id)
                return leaders_id, True
            else:
                return leaders_id, False

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
    for i in range(3):
        el = g1.election(g1.get_players(alive=1, type_result='int'))
        if not el[1]:
            g1.election(el[0], re_election=True)
        g1.update_table()
        g1.update_knowledge()
    print(g1.game_log)