import random
import pandas as pd
from enum import IntEnum

UNKNOWN = 0
YES = 1
NO = -1
RED = 1
BLACK = -1

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
                'sheriff':0, # значение о шерифстве игрока
                'vendetta':0, # (только для мафии) коэффициент неудобных мирных для мафии
                'alive':1, # жив ли игрок
                'lock':0 # зафиксировать подозрение к игроку
            }
        ).astype(
            {'suspection':'float32', 'sheriff':'Int8', 'vendetta':'float32',
             'alive':'Int8', 'lock':'Int8'})
        self.knowledge.drop(index=self.id, inplace=True)

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.role}'

    def get_players(self, alive:int=None, color:int=None, sheriff:int=None,
                    players_id:list[int]=None, sort=None):
        result = self.knowledge.copy()
        if alive is not None:
            result.query('alive == @alive', inplace=True)
        if color:
            sus = self.max_sus if color == BLACK else self.min_sus
            result.query('suspection == @sus and lock == 1', inplace=True)
        if sheriff is not None:
            result.query('sheriff == @sheriff', inplace=True)
        if players_id is not None:
            result.query('index in @players_id', inplace=True)
        return result.index.to_list()

    def get_target(self, players_id=None, by='suspection'):
        if players_id is None:
            players_id = self.knowledge.index.to_list()
        return self.knowledge.loc[players_id, by].idxmax()


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


if __name__== '__main__':
    p = Citizen(10)
    p.knowledge.loc[5, ['suspection', 'lock']] = [1, 1]
    p.knowledge.loc[3, ['suspection', 'lock']] = [5, 1]
    p.knowledge.loc[1, ['suspection', 'lock']] = [6, 1]
    p.knowledge.loc[2, ['suspection', 'lock']] = [7, 1]
    print(p.vote(candidates=[2, 3, 4, 5, 6, 7]))