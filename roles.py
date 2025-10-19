import random
import pandas as pd

'''
knowledge - параметр у каждого игрока, который определеяет его знания по поводу игроков
это словарь с id игроков и параметрами их знаний и мнения
id - идентификатор игрока от 1 до 10
для мирных игроков:
suspection - степень подозрения. В сумме все значения должны давать 3. Значения не могут превышать 1 и быть меньше -1.
Постоянно распределяется таким образом, чтобы сумма не была больше 3.
color - точный 100% цвет того или иного игрока. Если 1 - то красный, если -1 - то черный, если 0 - то неизвесный
seriff - точная информация что данный игрок является шерифом. Если 1 - то шериф, если -1 - то не шериф, если 0 - то неизвестно
'''

class Player:
    def __init__(self, id):
        self.id = id
        self.alive = True
        self.role = 'Мирный'
        self.knowledge = pd.DataFrame(
            index=range(1, 11),
            data={
            'suspection': [0] * 10,
            'color': 0,
            'seriff': 0,
            'alive': True
        })
        self.knowledge.loc[self.id, 'color'] = 1

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.role}'

    def target_for_vote(self, candidates) -> int:
        lvl1_candidates = list(set(candidates).intersection(self.exact_mafia))
        if len(lvl1_candidates) > 0:
            return random.choice(lvl1_candidates)
        else:
            return random.choice(candidates)

    def vote(self, target, vote_table):
        if isinstance(target, Player):
            target = target.id
        vote_table.loc[self.id, 'votes_for'] = target
        vote_table.loc[target, 'votes_recieved'] += 1
        return target.id

    @property
    def exact_citizens(self):
        return self.knowledge.query('alive and color == 1').index.to_list()

    @property
    def exact_mafia(self):
        return self.knowledge.query('alive and color == -1').index.to_list()

    @property
    def unknown_players(self):
        return self.knowledge.query('alive and color == 0').index.to_list()

    @property
    def seriff(self):
        return self.knowledge.query('alive and seriff == 1').index.max()

class MafiaPlayer(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Мафия'
        self.knowledge.loc[self.id, 'color'] = -1
        self.shot_assigner = False

    @property
    def unknown_seriff(self):
        return self.knowledge.query('alive and seriff == 0').index.to_list()

    def target_for_vote(self, candidates):
        lvl1_candidates = list(set(candidates).intersection(self.exact_citizens))
        if len(lvl1_candidates) > 0:
            return random.choice(lvl1_candidates)
        else:
            return random.choice(candidates)

    def target_for_shot(self):
        if self.seriff > 0:
            return self.seriff
        elif len(self.unknown_seriff) > 0:
            return random.choice(self.unknown_seriff)
        else:
            return random.choice(self.exact_citizens)

    def shot(self, target):
        target.alive = False
        return target

    def delegate_shooting(self, target):
        target.shot_assigner = True
        self.shot_assigner = False
        

class SeriffPlayer(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Шериф'
        self.found_all_mafia_flag = False
        self.knowledge.loc[:, 'seriff'] = -1
        self.knowledge.loc[self.id, 'seriff'] = 1
        self.knowledge.loc[self.id, 'color'] = 1

    def target_fot_check(self):
        return random.choice(self.unknown_players)

    def check(self, target) -> int:
        if self.found_all_mafia_flag:
            return None
        if isinstance(target, MafiaPlayer):
            self.knowledge.loc[target.id, 'color'] = -1
            if len(self.exact_mafia) == 3:
                self.found_all_mafia_flag = True
                self.knowledge['color'] = self.knowledge['color'].replace(0, 1)
            return True
        else:
            self.knowledge.loc[target.id, 'color'] = 1
            if len(self.exact_citizens) >= 7:
                self.foung_all_mafia_flag = True
                self.knowledge['color'] = self.knowledge['color'].replace(0, -1)
        return False


class DonPlayer(MafiaPlayer):
    def __init__(self, id):
        super().__init__(id)
        self.serif_id = 0
        self.role = 'Дон'
        self.shot_assigner = True

    def target_for_check(self):
        return random.choice(self.unknown_seriff)

    def check(self, target) -> int:
        if self.serif_id > 0:
            return
        if isinstance(target, SeriffPlayer):
            self.knowledge.loc[target.id, 'seriff'] = 1
            self.serif_id = target.id
            self.knowledge['seriff'] = self.knowledge['seriff'].replace(0, -1)
            return True
        else:
            self.knowledge.loc[target.id, 'seriff'] = -1
        return False


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

class Game:
    def __init__(self):
        self.table = Table()


    def day_voting(self):
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

class Election:
    def __init__(self, table: Table, re_election=False):
        self.candidates = table.alive_players()
        self.candidates_id = table.alive_players_id()
        self.re_election = re_election
        self.election_list = pd.DataFrame(
            index=self.candidates_id,
            columns=[
                'votes_for',
                'votes_recieved',
                'players_voted'
            ]
        )
        self.election_list['votes_for'] = 0
        self.election_list['votes_recieved'] = 0
        self.election_list['players_voted'] = []
        self.election_list.dtypes = {
            'votes_for': 'Int64',
            'votes_recieved' : 'Int64'
        }
        self.election_history = ''

    def message_to_history(self, event, players):
        if self.election_history != '':
            self.election_history += '\n'
        players = ','.join(str(p) for p in players)
        match event:
            case 'declare':
                self.election_history += (
                    'Объявлено голосование между игроками ' + players)

    def voting_process(self):
        self.election_history('declare', self.candidates)
        for p in self.candidates:
            p.vote(p.target_for_vote(self.candidates_id), self.election_list)
            
        max_votes = self.election_list['votes_recieved'].max()
        leaders = self.election_list.query('votes_recieved == @max_votes')\
            .index.to_list()
        if len(leaders) == 1:
            self.table.players[leaders[0]].alive = False
            print('На голосовании единогласно был выбран игрок ' + str(leaders[0]))
            return leaders, True # True означает, что голосование проведено 
        else:
            print('Голоса поделились между игроками ' + ','.join(str(l) for l in leaders))
            if second_round:
                if random.random() > 0.5:
                    for l in leaders:
                        l.alive = False
                        print('Большинство игроков проголосовало за подъем ')
                    return leaders, True
                else:
                    print('Большинство игроков проголосовало за оставление ')
                return [], True
            else:
                print('Будет объявлено переголосование')
                return leaders, False



if __name__=='__main__':
    print('Добро пожаловать в интеллектуально-психологическую игру "Мафия"')
    g = Game()
    print(g.table.players)
    g.day_voting()
    pass
'''
Проблема при голосовании
Проголосовавший игрок попадает в vote_Table с votes_recieved = Nan
Далее, так как он там, то он становится целью для следующих голосований
Решение - передавать в target_for_vote только кандидатов
'''