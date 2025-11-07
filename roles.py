import random
import numpy as np
import pandas as pd
from enum import IntEnum

UNKNOWN = 0
YES = 1
NO = -1
# color
RED = 1
BLACK = -1
# qiut_reason
KILLED = 2
JAILED = 1
ALIVE=0

class Player:
    total_sus = 36
    max_sus = total_sus / 3
    base_sus = total_sus / 9
    min_sus = 0
    def __init__(self, id:int):
        self.id = id
        self.alive = True
        self.role = 'player'
        self.knowledge = pd.DataFrame(
            index=list(range(1, 11)),
            data={
                'suspection':self.base_sus, # коэффициент подозрения
                'sheriff':UNKNOWN, # значение о шерифстве игрока
                'vendetta':0, # (только для мафии) коэффициент неудобных мирных для мафии
                'lock':UNKNOWN, # зафиксировать подозрение к игроку
                'alive':YES, # живой игрок
                'quit':0 # состояние (жив, убит, заголосован)
            }
        ).astype(
            {'suspection':'float32', 'sheriff':'Int8', 'vendetta':'float32',
             'quit':'Int8', 'lock':'Int8'})
        self.knowledge.drop(index=self.id, inplace=True)
        self.mafia_detected = False

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.rouele}'

    def get_players(self, alive:int=None, color:int=None, sheriff:int=None,
                    lock:int=None, quit:int=None, players_id:list[int]=None,
                    exclude_players_id:list[int]=None):
        result = self.knowledge.copy()
        if alive is not None:
            result.query('alive == @alive', engine='python', inplace=True)
        if color is not None:
            match color:
                case 0:
                    result.query('lock == 0', engine='python', inplace=True)
                case -1:
                    result.query('lock == 1 and suspection == 12', engine='python', inplace=True)
                case 1:
                    result.query('lock == 1 and suspection == 0', engine='python', inplace=True)
        if sheriff is not None:
            result.query('sheriff == @sheriff', inplace=True, engine='python')
        if players_id is not None:
            result.query('index in @players_id', inplace=True, engine='python')
        if exclude_players_id is not None:
            result.query('index not in @exclude_players_id', inplace=True, engine='python')
        if lock is not None:
            result.query('lock == @lock', inplace=True, engine='python')
        if quit is not None:
            result.query('quit==@quit', inplace=True, engine='python')
        return result.index.to_list()

    def get_target(self, players_id=None, by='suspection'):
        if players_id is None:
            players_id = self.knowledge.index.to_list()
        return self.knowledge.loc[players_id, by].idxmax()

    def change_sus(self, index, value): 
        if not isinstance(index, list):
            index = [index]
        changed_fact = 0
        for i in index:
            cur_sus = self.knowledge.loc[i, 'suspection']
            if value > 0:
                real_value = min(value, self.max_sus - cur_sus)
            else:
                real_value = max(value, -cur_sus)
            self.knowledge.loc[i, 'suspection'] += np.float32(real_value)
            changed_fact += np.float32(real_value)
        self.round_sus()
        return changed_fact

    def share_sus(self, index, value):
        if isinstance(index, int):
            index = [index]
        target_group = self.get_players(lock=0, players_id=index)
        n_players = len(target_group)
        if n_players == 0:
            return 0
        shared_sus = value / n_players
        value -= self.change_sus(target_group, shared_sus)
        self.round_sus()
        return value

    def suspect(self, index, value):
        if isinstance(index, int):
            index = [index]
        align_group = self.get_players(lock=0, exclude_players_id=index)
        target_group = self.get_players(lock=0, players_id=index)
        if abs(value) > 0:
            rest_value = -self.change_sus(target_group, value)
            while abs(rest_value) > 0.02:
                rest_value = self.share_sus(align_group, rest_value)
        self.round_sus()

    def set_sus(self, index, value, lock=False):
        if isinstance(index, int):
            index = [index]
        align_group = self.get_players(lock=0, exclude_players_id=index)
        rest_value = self.knowledge.loc[index, 'suspection'].sum() - len(index) * value
        self.knowledge.loc[index, 'suspection'] = value
        while abs(rest_value) > 0.02:
            rest_value = self.share_sus(align_group, rest_value)
        if lock:
            self.knowledge.loc[index, 'lock'] = YES
        self.round_sus()

    def set_killed(self, index:int, sheriff=NO):
        self.set_sus(index, self.min_sus)
        self.knowledge.loc[index, 
            ['sheriff', 'lock', 'alive', 'quit']
        ] = [sheriff, YES, NO, KILLED]

    def set_jailed(self, index, sheriff=NO):
        self.knowledge.loc[index, ['sheriff', 'alive', 'quit']] = [
            sheriff, NO, JAILED]

    def round_sus(self):
        if self.knowledge.suspection.sum() < self.total_sus:
            self.knowledge.suspection = np.ceil(self.knowledge.suspection * 100) / 100
        if self.knowledge.suspection.sum() > self.total_sus:
            self.knowledge.suspection = np.floor(self.knowledge.suspection * 100) / 100

    def set_exact_color(self, index, color):
        if isinstance(index, int):
            index = [index]
        value = self.max_sus if color == BLACK else RED
        self.set_sus(index, value)
        self.knowledge.loc[index, 'lock'] = YES

class Citizen(Player):
    def __init__(self, id:int):
        super().__init__(id)
        self.role='Citizen'

    def vote(self, candidates:list[int]) -> int:
        return self.get_target(players_id=candidates, by='suspection')

class Sheriff(Citizen):
    def __init__(self, id:int):
        super().__init__(id)
        self.role = 'Sheriff'
        self.mission_completed = False
        self.knowledge.loc[:, 'sheriff'] = NO

# counting will be in special method
    def check(self) -> int:
        if self.mission_completed:
            return 0
        elif len(self.get_players(color=BLACK)) == 3:
            self.mission_completed = True
        elif len(self.get_players(color=RED)) == 6:
            self.mission_completed = True
        else:
            return self.get_target(
                players_id=self.get_players(alive=YES, color=UNKNOWN),
                by='suspection')
        return 0

class Mafia(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Mafia'
        self.shot_assigner = False

    def vote(self, candidates:list[int]) -> int:
        return self.get_target(players_id=candidates, by='vendetta')
    
    def shot(self) -> int:
        result = self.get_players(alive=YES, sheriff=YES)
        if len(result) > 0: # стреляется шериф
            return result[0]
        result = self.get_players(alive=YES, sheriff=UNKNOWN)
        if len(result) > 0: # стреляется любой мирный, возможно шериф
            return self.get_target(players_id=result, by='vendetta')
        # стреляется любой живой красный игрок
        return self.get_target(self.get_players(alive=YES), by='vendetta')


class Don(Mafia):
    def __init__(self, id:int):
        super().__init__(id)
        self.role = 'Don'
        self.shot_assigner = True
        self.mission_completed = False

    def check(self) -> int:
        if self.mission_completed:
            return 0
        elif self.get_players(sheriff=YES):
            self.mission_completed = True
            self.knowledge.loc[self.get_players(sheriff=UNKNOWN), 'sheriff'] = NO
        elif len(self.get_players(sheriff=NO)) == 6:
            self.mission_completed = True
            self.knowledge.loc[self.get_players(sheriff=UNKNOWN), 'sheriff'] = YES
        else:
            return self.get_target(
                players_id=self.get_players(alive=YES, sheriff=UNKNOWN),
                by='suspection')

a = Citizen(4)
print(Player.count_mapping)
a.set_sus([7, 8], 12, True)
for i in range(5, 10):
    a.set_jailed(i)
print(a.knowledge)
print(a.knowledge.suspection.sum())

# BUG когда в 0 пилим пятерых игроков и поднимаем, при этом знаем, что два 
# игрока в подъеме точно мафия, то получем некорректный счет
# подозрение распределяется среди попиленных неизвестных и живых неизвестных
# хотя игра должна понимать, что если игра продолжается, значит за столом есть
# только одна мафия, значит это подозрение надо распределить только
# среди оставшихся игроков
# TODO счет должен вестись отдельно среди покинувших игру и среди живых.
# алгоритм:
# 1. Понять, сколько мафии точно.
# Если точной инфы нет, ведем счет как прежде
# Если одна мафия точно покинула стол, круг при семерых, то
# внедряем маппинг для счета, чтобы упростить код