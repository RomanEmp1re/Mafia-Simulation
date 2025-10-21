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
        self.role = 'игрок'
        self.knowledge = pd.DataFrame(
            index=range(1, 11),
            data={
            'color': 0, # 1 - мирный, 0 - неизвестно, -1 - мафия
            'seriff': 0, # 1 - шериф, 0 - неизвестно, -1 - не шериф
            'alive': 1 # 1 - жив, -1 - покинул игру
        })
        self.knowledge.drop(self.id, inplace=True)

    def __str__(self):
        return f'Игрок #{self.id}, роль - {self.role}'

    def get_players(self, alive=None, color=None, seriff=None, players_id=None):
        result = self.knowledge.copy()
        if alive is not None:
            result.query('alive == @alive', inplace=True)
        if color is not None:
            result.query('color == @color', inplace=True)
        if seriff is not None:
            result.query('seriff == @seriff', inplace=True)
        if players_id is not None:
            result.query('index in @players_id', inplace=True)
        return result.index.to_list()


class Citizen(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role='Мирный'

    def vote(self, candidates):
        result = self.get_players(color=-1, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        result = self.get_players(color=0, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        result = self.get_players(players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(candidates)


class Seriff(Citizen):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Шериф'
        self.mission_completed = False
        self.knowledge.loc[:, 'seriff'] = -1

    def check(self) -> int:
        if self.mission_completed:
            return 0 # когда миссия зевершена
        if len(self.get_players(color=-1)) == 3:
            self.mission_completed = True
            self.knowledge['color'].replace(0, 1, inplace=True)
            return 0
        if len(self.get_players(color=1)) == 6:
            self.mission_completed = True
            self.knowledge['color'].replace(0, -1, inplace=True)
            return 0 # когда найдена вся мафия или все мирные
        result = self.get_players(alive=1, color=0)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(self.get_players(color=0))


class Mafia(Player):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Мафия'
        self.shot_assigner = False

    def vote(self, candidates):
        result = self.get_players(color=1, players_id=candidates)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(players_id=candidates)
    
    def shot(self):
        result = self.get_players(alive=1, seriff=1)
        if len(result) > 0: # стреляется шериф
            return random.choice(result)
        result = self.get_players(alive=1, seriff=0)
        if len(result) > 0: # стреляется любой мирный, возможно шериф
            return random.choice(result)
        # стреляется любой живой красный игрок
        return random.choice(self.get_players(alive=1, color=1))


class Don(Mafia):
    def __init__(self, id):
        super().__init__(id)
        self.role = 'Дон'
        self.shot_assigner = True
        self.mission_completed = False

    def check(self):
        if self.mission_completed:
            return 0
        if self.get_players(seriff=1):
            self.mission_completed = True
            self.knowledge['seriff'].replace(0, -1, inplace=True)
            return 0
        result = self.get_players(alive=1, seriff=0)
        if len(result) > 0:
            return random.choice(result)
        return random.choice(self.get_players(seriff=0))