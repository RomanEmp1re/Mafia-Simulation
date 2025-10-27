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
    total_suspection = 9
    max_suspection = total_suspection / 3
    min_suspction = 0
    def __init__(self, player_id):
        self.knowledge = pd.DataFrame(
            index=list(range(1, 11)),
            data={
                'color':0, # точное знание о цвете игрока
                'suspection':1, # коэффициент подозрения
                'sheriff':0, # значение о шерифстве игрока
                'vendetta':0, # (только для мафии) коэффициент неудобных мирных для мафии
            }
        )
        self.knowledge = self.knowledge.astype({'color':'Int8', 'suspection':'float32',
            'sheriff':'Int8', 'vendetta':'float32'})
        self.knowledge.drop(index=player_id, inplace=True)
    
    def adjust_suspection(self, player_id, value):
        control_group = self.knowledge[self.knowledge['color'] == 0]['suspection'].copy()
        current_suspection = control_group[player_id]
        if value >= 0:
            real_value = min(value, self.max_suspection - current_suspection)
        else:
            real_value = max(value, -current_suspection - self.min_suspction)
        control_group[player_id] += real_value
        adjust_value = real_value / control_group.count()
        control_group.loc[control_group.index != player_id] -= adjust_value
        self.knowledge.update(control_group)


if __name__=='__main__':
    s = Knowledge(1)
    s.adjust_suspection(2, 3)
    s.adjust_suspection(5, 3)
    s.adjust_suspection(4, 3)
    print(s.knowledge)
    