import pandas as pd
import numpy as np

class Knowledge:
    total_sus = 36
    max_sus = total_sus / 3
    base_sus = total_sus / 9
    min_sus = 0
    def __init__(self, player_id):
        self.table = pd.DataFrame(
            index=list(range(1, 11)),
            data={
                'suspection':self.base_sus, # коэффициент подозрения
                'sheriff':0, # значение о шерифстве игрока
                'vendetta':0, # (только для мафии) коэффициент неудобных мирных для мафии
                'alive':1, # жив ли игрок
                'lock':0 # зафиксировать цвет игрока
            }
        )
        self.table = self.table.astype(
            {'suspection':'float32', 'sheriff':'Int8', 'vendetta':'float32',
             'alive':'Int8', 'lock':'Int8'})
        self.table.drop(index=player_id, inplace=True)

    def change_sus(self, index, value): 
        if not isinstance(index, list):
            index = [index]
        changed_fact = 0
        for i in index:
            cur_sus = self.table.loc[i, 'suspection']
            if value > 0:
                real_value = min(value, self.max_sus - cur_sus)
            else:
                real_value = max(value, -cur_sus)
            self.table.loc[i, 'suspection'] += np.float32(real_value)
            changed_fact += np.float32(real_value)
        return changed_fact

    def share_sus(self, index, value):
        if value > 0:
            target_group = self.table\
                .query('index in @index and lock == 0 and suspection < @self.max_sus')\
                .index.to_list()
        elif value < 0:
            target_group = self.table\
                .query('index in @index and lock == 0 and suspection > @self.min_sus')\
                .index.to_list()
        n_players = len(target_group)
        if n_players == 0:
            return 0
        shared_sus = value / n_players
        value -= self.change_sus(target_group, shared_sus)
        return value

    def adjust_sus(self, index, value):
        if isinstance(index, int):
            index = [index]
        align_group = self.table\
            .query('lock == 0 and index not in @index').index.to_list()
        target_group = self.table\
            .query('lock == 0 and index in @index').index.to_list()
        if abs(value) > 0:
            rest_value = -self.change_sus(target_group, value)
            while abs(rest_value) > 0.0001:
                rest_value = self.share_sus(align_group, rest_value)
        else:
            return

    def set_sus(self, index, value, lock=False):
        if isinstance(index, int):
            index = [index]
        align_group = self.table\
            .query('lock == 0 and index not in @index').index.to_list()
        rest_value = self.table.loc[index, 'suspection'].sum() - len(index) * value
        self.table.loc[index, 'suspection'] = value
        while abs(rest_value) > 0.0001:
            rest_value = self.share_sus(align_group, rest_value)
        if lock:
            self.table.loc[index, 'lock'] = 1