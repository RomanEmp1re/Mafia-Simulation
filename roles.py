import random
import pandas as pd
from enum import IntEnum

'''
knowledge - параметр у каждого игрока, который определеяет его знания по поводу игроков
это словарь с id игроков и параметрами их знаний и мнения
id - идентификатор игрока от 1 до 10
для мирных игроков:
Постоянно распределяется таким образом, чтобы сумма не была больше 3.
color - точный 100% цвет того или иного игрока. Если 1 - то красный, если -1 - то черный, если 0 - то неизвесный
sheriff - точная информация что данный игрок является шерифом. Если 1 - то шериф, если -1 - то не шериф, если 0 - то неизвестно
'''

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
            self.knowledge['color'].replace(UNKNOWN, RED, inplace=True)
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
            self.knowledge['sheriff'].replace(UNKNOWN, NO, inplace=True)
            return 0
        result = self.get_players(alive=YES, sheriff=UNKNOWN)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(self.get_players(sheriff=UNKNOWN))

if __name__=='__main__':
    p1 = Mafia(1)
    p1.knowledge.loc[[2, 3], ['color', 'sheriff']] = [-1, -1]
    p1.knowledge.loc[4:10, ['color', 'sheriff']] = [1, 0]
    stest = set()
    for i in range(50):
        stest.add(p1.shot())
    print(stest)