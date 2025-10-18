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
    table = None # сюда будет помещен стол, чтобы доставать роли
    def __init__(self, id):
        self.id = id
        self.alive = True
        self.votes_got = 0
        self.role = 'Мирный'
        self.knowledge = pd.DataFrame(
            index=range(1, 11),
            data={
            'suspection': [0] * 10,
            'color': 0,
            'seriff': 0
        })
        self.knowledge.loc[self.id, 'color'] = 1

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.role}'

    def target_for_vote(self) -> int:
        if isinstance(target, int):
            target = self.table[target]
        if len(self.exact_mafia) > 0:
            return random.choice(self.exact_mafia)
        else:
            return random.choice(self.unknown_players)

    def vote(self, game_state) -> int:
        target = self.target_for_vote(game_state)
        target.votes_got += 1

    @property
    def exact_citizens(self):
        return self.knowledge[self.knowledge['color'] == 1].index.to_list()

    @property
    def exact_mafia(self):
        return self.knowledge[self.knowledge['color'] == -1].index.to_list()

    @property
    def unknown_players(self):
        return self.knowledge[self.knowledge['color'] == 0].index.to_list()

    @property
    def seriff(self):
        return self.knowledge[self.knowledge['seriff'] == 1].index.max()

class MafiaPlayer(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Мафия'
        self.knowledge.loc[self.id, 'color'] = -1

    def shot(self, target) -> int:
        target.alive = False
        return target.id

    @property
    def unknown_citizen(self):
        return self.knowledge[
            self.knowledge['seriff'] == 0
        ].index.to_list()

    def target_for_vote(self):
        return random.choice(self.exact_citizens)

    def target_for_shot(self):
        if isinstance(target, int):
            target = self.table[target]
        if len(self.exact_serif) > 0:
            return self.exact_serif
        else:
            return random.choice(self.exact_citizens)


class SeriffPlayer(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Шериф'
        self.found_all_mafia_flag = False
        self.knowledge.loc[:, 'seriff'] = -1
        self.knowledge.loc[self.id, 'seriff'] = 1
        self.knowledge.loc[self.id, 'color'] = 1

    def pick_verify(self):
        return random.choice(self.unknown_players)

    def check(self, target) -> int:
        if isinstance(target, int):
            target = self.table[target]
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

    def pick_verify(self):
        return random.choice(self.unknown_citizen)

    def check(self, target) -> int:
        if isinstance(target, int):
            target = self.table[target]
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

    def shoose_victim(self, game_state):
        if self.serif_id == 0:
            target = random.choice(game_state.citizen_players)
            return target.id
        else:
            return self.serif_id


class GameState:
    days_count = 0
    roles = [MafiaPlayer] * 2 + [DonPlayer] + [Player] * 6 + [SeriffPlayer]
    random.shuffle(roles)
    players = pd.Series(
        index=range(1, 11),
        data=[None]*10
    )
    for i in players.index:
        players[i] = roles[i - 1](i)
    info_table = pd.DataFrame(
        index=range(1, 11),
        data = {
            'color': map(lambda x : -1 if isinstance(x, MafiaPlayer) else 1, players),
            'seriff': map(lambda x : 1 if isinstance(x, SeriffPlayer) else -1, players)
        }
    )
        
    def __init__(self):
        self.days_count += 1
        self.day = self.days_count
        if self.day == 1:
            Player.table = self.players
            for i in self.players:
                if isinstance(i, MafiaPlayer):
                    i.knowledge['color'] = self.info_table['color']
    
    @property
    def alive_players(self):
        return [p for p in self.players if p.alive]

    @property
    def alive_players_id(self):
        return [p.id for p in self.players if p.alive]

    @property
    def alive_count(self):
        return len(self.alive_players)

    @property
    def mafia_players(self):
        return [p for p in self.alive_players if type(p) in (MafiaPlayer, DonPlayer)]

    @property
    def mafia_players_id(self):
        return [p.id for p in self.alive_players if type(p) in (MafiaPlayer, DonPlayer)]

    @property
    def citizen_players(self):
        return [p for p in self.alive_players if type(p) not in [MafiaPlayer, DonPlayer]]

    @property
    def citizen_players_id(self):
        return [p.id for p in self.alive_players if type(p) not in [MafiaPlayer, DonPlayer]]

    @property
    def don(self):
        return [p for p in self.alive_players if isinstance(p, DonPlayer)][0]

    @property
    def don_id(self):
        return [p.id for p in self.alive_players if isinstance(p, DonPlayer)][0]

    @property
    def seriff(self):
        return [p for p in self.alive_players if isinstance(p, SeriffPlayer)][0]

    @property
    def seriff_id(self):
        return [p.id for p in self.alive_players if isinstance(p, SeriffPlayer)][0]

if __name__=='__main__':
    print('Добро пожаловать в интеллектуально-психологическую игру "Мафия"')
    g1 = GameState()
    print(g1.players)
    pass
