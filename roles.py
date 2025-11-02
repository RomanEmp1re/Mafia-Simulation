import random
import pandas as pd
from enum import IntEnum

ALIVE = 1
BLACK = -1
RED = 1
UNKNOWN = 0
YES = 1
NO = - 1


class Player:
    def __init__(self, id:int):
        self.id = id
        self.alive = True
        self.role = 'player'
        self.knowledge = pd.DataFrame(
            index=range(1, 11),
            data={
            'color': UNKNOWN, # 1 - мирный, 0 - неизвестно, -1 - мафия
            'sheriff': UNKNOWN, # 1 - шериф, 0 - неизвестно, -1 - не шериф
            'alive': YES # 1 - жив, -1 - покинул игру
        })
        self.knowledge.drop(self.id, inplace=True)

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.role}'

    def get_players(self, alive:int=None, color:int=None, sheriff:int=None,
                    players_id:list[int]=None):
        result = self.knowledge.copy()
        if alive is not None:
            result.query('alive == @alive', inplace=True)
        if color is not None:
            result.query('color == @color', inplace=True)
        if sheriff is not None:
            result.query('sheriff == @sheriff', inplace=True)
        if players_id is not None:
            result.query('index in @players_id', inplace=True)
        return result.index.to_list()


class Citizen(Player):
    def __init__(self, id:int):
        super().__init__(id)
        self.role='Citizen'

    def vote(self, candidates:list[int]) -> int:
        result = self.get_players(color=BLACK, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        result = self.get_players(color=UNKNOWN, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        result = self.get_players(players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(candidates)


class Sheriff(Citizen):
    def __init__(self, id:int):
        super().__init__(id)
        self.role = 'Sheriff'
        self.mission_completed = False
        self.knowledge.loc[:, 'sheriff'] = -1

    def check(self) -> int:
        if self.mission_completed:
            return 0 # когда миссия зевершена
        if len(self.get_players(color=BLACK)) == 3:
            self.mission_completed = True
            self.knowledge['color'] = self.knowledge['color'].replace(UNKNOWN, RED)
            return 0
        if len(self.get_players(color=RED)) == 6:
            self.mission_completed = True
            self.knowledge['color'].replace(UNKNOWN, RED, inplace=True)
            return 0 # когда найдена вся мафия или все мирные
        result = self.get_players(alive=YES, color=UNKNOWN)
        if len(result) > 0:
            return random.choice(result)
        result = self.get_players(color=UNKNOWN)
        return random.choice(result)


class Mafia(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Mafia'
        self.shot_assigner = False

    def vote(self, candidates:list[int]) -> int:
        result = self.get_players(color=RED, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(candidates)
    
    def shot(self) -> int:
        result = self.get_players(alive=YES, sheriff=YES)
        if len(result) > 0: # стреляется шериф
            return random.choice(result)
        result = self.get_players(alive=YES, sheriff=UNKNOWN)
        if len(result) > 0: # стреляется любой мирный, возможно шериф
            return random.choice(result)
        # стреляется любой живой красный игрок
        return random.choice(self.get_players(alive=YES, color=RED))


class Don(Mafia):
    def __init__(self, id:int):
        super().__init__(id)
        self.role = 'Don'
        self.shot_assigner = True
        self.mission_completed = False

    def check(self) -> int:
        if self.mission_completed:
            return 0
        if self.get_players(sheriff=YES):
            self.mission_completed = True
            self.knowledge['sheriff'] = self.knowledge['sheriff'].replace(UNKNOWN, NO)
            return 0
        result = self.get_players(alive=YES, sheriff=UNKNOWN)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(self.get_players(sheriff=UNKNOWN))

class Knowledge:
    total_suspection = 36
    max_suspection = total_suspection / 3
    base_suspection = total_suspection / 9
    min_suspection = 0
    def __init__(self, player_id):
        self.knowledge = pd.DataFrame(
            index=list(range(1, 11)),
            data={
                'suspection':self.base_suspection, # коэффициент подозрения
                'sheriff':0, # значение о шерифстве игрока
                'vendetta':0, # (только для мафии) коэффициент неудобных мирных для мафии
                'alive':1, # жив ли игрок
                'lock':0 # зафиксировать цвет игрока
            }
        )
        self.knowledge = self.knowledge.astype(
            {'suspection':'float32', 'sheriff':'Int8', 'vendetta':'float32',
             'alive':'Int8', 'lock':'Int8'})
        self.knowledge.drop(index=player_id, inplace=True)

    def get_players(self, alive:int=None, lock:int=None, sheriff:int=None,
            players_id:list[int]=None, as_df=False):
        result = self.knowledge.copy()
        if alive is not None:
            result.query('alive == @alive', inplace=True)
        if lock is not None:
            result.query('lock == @lock', inplace=True)
        if sheriff is not None:
            result.query('sheriff == @sheriff', inplace=True)
        if players_id is not None:
            result.query('index in @players_id', inplace=True)
        if as_df:
            return result
        else:
            return result.index.to_list()

    @property
    def rest_suspection(self):
        cnt_alive = self.get_plaeyrs(alive=1)
        if cnt_alive >= 7:
            cnt_black = 3
        elif cnt_alive >= 5:
            cnt_black = 2
        elif cnt_alive >= 3:
            cnt_black = 1
        for i in self.get_players(color=-1):
            cnt_black -= 1
        return cnt_black * self.max_suspection
    
    def increase_sus(self, player_id, value):
        control_group = self.knowledge.query('lock == 0 and suspection > 0 and alive = 1')
        control_group = control_group.loc[control_group.index != player_id]
        current_suspection = self.knowledge.loc[player_id, 'suspection']
        if value == 0 or current_suspection == self.max_suspection:
            return
        real_value = min(value, self.max_suspection - current_suspection)
        self.knowledge.loc[player_id, 'suspection'] += real_value
        shared_value = real_value / control_group.count()
        while real_value > 0:
            for i in control_group:
                if i < shared_value:
                    extra_value += shared_value - i
                    i['suspection'] = 0
    
    def split_sus(self, control_group, value):
        for i in control_group:

    def apply_suspection(self, player_id, value):
        control_group = self.get_players(lock=0, as_df=True)['suspection']
        control_group = control_group.loc[control_group.index != player_id]
        current_suspection = self.knowledge.loc[player_id, 'suspection']
        if value > 0 and current_suspection == self.max_suspection:
            return
        if value < 0 and current_suspection == self.min_suspection:
            return
        if value >= 0:
            real_value = min(value, self.max_suspection - current_suspection)
        else:
            real_value = max(value, -current_suspection - self.min_suspection)
        self.knowledge.loc[player_id, 'suspection'] += real_value
        adjust_value = real_value / control_group.count()
        control_group = control_group - adjust_value
        control_group = control_group.clip(self.min_suspection, self.max_suspection)
        self.knowledge.update(control_group)

    def set_exact_color(self, player_id, color):
        self.knowledge.loc[player_id, 'lock'] = 1
        if color == 1:
            self.apply_suspection(player_id, -self.max_suspection)
        elif color == -1:
            self.apply_suspection(player_id, self.max_suspection)
    

if __name__== '__main__':
    s = Knowledge(1)
    s.apply_suspection(2, 3)
    s.set_exact_color(7, 1)
    s.set_exact_color(8, -1)
    s.set_exact_color(9, -1)
    s.set_exact_color(10, -1) # все коэффициенты должны учесть относительность друг друга
    print(s.knowledge)
    print(s.knowledge['suspection'].sum())
    