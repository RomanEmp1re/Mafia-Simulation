from roles import *
import random
import pandas as pd
import yaml


class Game:
    table_template = pd.DataFrame(
        index=range(1, 11),
        data={
            'color':UNKNOWN, 'sheriff':UNKNOWN, 'role':UNKNOWN, 
            'alive':UNKNOWN, 'quit':UNKNOWN,
        }
    ).astype({'color':'Int8', 'sheriff':'Int8', 'role':'object', 'alive':'Int8',
             'quit':'Int8'})
    common_knowledge_template = pd.DataFrame(
        index=range(1, 11),
        data={'color':UNKNOWN, 'sheriff':UNKNOWN, 'alive':YES, 'quit':UNKNOWN}
    ).astype({'color':'Int8', 'sheriff':'Int8', 'alive':'Int8', 'quit':'Int8'})

    def __init__(self, custom_roles:dict=None):
        self.game_log = 'Добро пожаловать в интеллектуально'\
            '-психологическую игру Мафия!'
        mafia_cards = [Mafia] * 2
        sheriff_cards = [Sheriff]
        citizen_cards = [Citizen] * 6
        don_cards = [Don]
        self.players = pd.Series(
            index=range(1, 11),
            data=None
        ).astype('object')
        if custom_roles is not None:
            for role, players_list in custom_roles.items():
                for p in players_list:
                    match role:
                        case 'don':
                            self.players[p] = don_cards.pop()(p)
                        case 'mafia':
                            self.players[p] = mafia_cards.pop()(p)
                        case 'sheriff':
                            self.players[p] = sheriff_cards.pop()(p)
                        case 'citizen':
                            self.players[p] = citizen_cards.pop()(p)
        all_cards = mafia_cards + sheriff_cards + don_cards + citizen_cards
        random.shuffle(all_cards)
        if len(all_cards) > 0:
            for p in self.players[self.players.isna()].index:
                self.players[p] = all_cards.pop()(p)
        self.table = self.table_template.copy()
        for p in self.players:
            self.table.loc[p.id, :] = {
                'color' : BLACK if isinstance(p, Mafia) else RED,
                'sheriff' : YES if isinstance(p, Sheriff) else NO,
                'role' : p.role,
                'alive' : YES,
                'quit' : UNKNOWN
            }
        self.log('roles')
        for i in self.get_players(color=BLACK):
            i.knowledge['color'] = self.table['color']
            i.knowledge['suspection'] = self.table['color'].map(
                {BLACK:Player.max_sus, RED:Player.min_sus}) 
            i.knowledge.loc[i.get_players(color=BLACK), 'sheriff'] = NO
        self.log('mafia_talk')
        self.log('sheriff_sign')
        self.common_knowledge = self.common_knowledge_template.copy()

    @property
    def pretty_table(self, alive_only=False):
        return self.table.assign(
            quit=self.table.quit.map({
                UNKNOWN:'',
                JAILED:'jailed',
                KILLED:'killed'
            })
        )[['role', 'quit']]

    # выборка игроков по признаку
    def get_players(self, color=None, role=None, alive=None,
        quit=None, type_result='obj'):
        result = self.table.copy()
        if color is not None:
            result.query('color == @color',  inplace=True, engine='python')
        if role is not None:
            result.query('role == @role',  inplace=True, engine='python')
        if alive is not None:
            result.query('alive == @alive',  inplace=True, engine='python')
        if quit is not None:
            result.query('quit == @quit',  inplace=True, engine='python')
        match type_result:
            case 'obj':
                return self.players[result.index]
            case 'int':
                return result.index.to_list()
            case 'str':
                return ' '.join(result.index.astype('string').to_list())
            case 'df':
                return result
            case 'cute':
                return self.pretty_table.loc[result.index]

    # ведение лога игры
    def log(self, event, **kwargs):
        self.game_log += '\n'
        match event:
            case 'roles':
                self.game_log += f'Карты розданы, в игре у игроков следующие роли:\n{self.pretty_table['role']}'
            case 'mafia_talk':
                self.game_log += (
                    'Мафия знакомится, черная команда: ' +
                    self.get_players(color=-1, type_result='str') +
                    ', дон игры — ' + self.get_players(role='Don', type_result='str')
                )
            case 'sheriff_sign':
                self.game_log += (
                    'Шериф игры — ' +
                    self.get_players(role='Sheriff', type_result='str')
                )
            case 'hunt':
                victim = kwargs['victim']
                self.game_log += f'Этой ночью был убит игрок {victim}'
            case 'declare_election':
                players = ' '.join(str(i) for i in kwargs['players'])
                self.game_log += f'Объявлено голосование между игроками {players}'
            case 'vote':
                players = ' '.join([str(p) for p in kwargs['players']])
                victim = str(kwargs['victim'])
                self.game_log += f'  За игрока {victim} проголосовали игроки {players}'
            case 'leader':
                victim = str(kwargs['victim'])
                self.game_log += f'  Лидером голосования стал игрок {victim}'
            case 'share':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'  Голоса разделились поровну между игроками {players}'
            case 'mass':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'  Ставится вопрос о подъеме игроков {players}'
            case 'lift':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'  Было принято решение о подъеме игроков {players}'
            case 'leave':
                players = ' '.join(str(p) for p in kwargs['players'])
                self.game_log += f'  Было принято решение оставить игроков {players}'
            case 'reelection':
                players = ' '.join(str(p) for p in kwargs['candidates'])
                self.game_log += f'Объявлено переголосование между игроками {players}'  
            case 'don_check':
                result = 'шериф' if kwargs['result'] == 1 else 'не шериф'
                target = str(kwargs['target'])
                self.game_log += f'Дон проверяет игрока {target}. Игрок {target} - {result}'
            case 'sheriff_check':
                result = 'красный' if kwargs['result'] == 1 else 'черный'
                target = str(kwargs['target'])
                self.game_log += f'Шериф проверяет игрока {target}. Игрок {target} - {result}'
            case 'mafia_won':
                self.game_log += 'Мафия выиграла!'
            case 'city_won':
                self.game_log += 'Выграл мирный город'

    # ночной отстрел
    def hunt(self):
        for m in self.get_players(color=BLACK, alive=YES):
            if m.shot_assigner:
                target = m.shot()
                self.log(event='hunt', victim=target)
                return target

    # проверка дона
    def don_check(self):
        player = self.get_players(role='Don').iat[0]
        target = player.check()
        if target:
            result = self.table.loc[target, 'sheriff']
            player.knowledge.loc[target, 'sheriff'] = result
            if result == YES:
                player.set_sheriff(target)
            self.log('don_check', target=target, result=result)

    # проверка шерифа
    def sheriff_check(self):
        player = self.get_players(role='Sheriff').iat[0]
        target = player.check()
        if target:
            result = self.table.loc[target, 'color']
            player.set_exact_color(index=target, color=result)
            self.log('sheriff_check', target=target, result=result)

    # актуализация знаний жителей
    def update_players_knowledge(self):
        for p in self.players:
            p.knowledge.update(self.common_knowledge.query('color != @UNKNOWN'))

    # заголосование игрока
    def jail_player(self, id):
        self.players[id].avlie = False
        self.table.loc[id, ['alive', 'quit']] = [NO, JAILED]
        if self.players[id].role == 'mafia' and self.players[id].shot_assigner:
            self.reassign_shoter()
        return id

    # ночной отстрел игрока
    def kill_player(self, id):
        victim = self.players[id]
        victim.alive = False
        self.table.loc[id, ['alive', 'quit']] = [NO, KILLED]
        if self.players[id].role in ('Mafia', 'Don'):
            if self.players[id].shot_assigner:
                self.reassign_shoter()
        return id

    # переназначение мафии, которая будет давать отстрел
    def reassign_shoter(self):
        mafia_list = self.get_players(role='Mafia', alive=YES, type_result='int')
        if mafia_list:
            inherits_power = random.choice(mafia_list)
            self.players[inherits_power].shot_assigner = True

    # вскрытие шерифа
    def sheriff_confess(self):
        sheriff = self.get_players(role='Sheriff').iat[0]
        self.common_knowledge.loc[sheriff.id, ['color', 'Sheriff']] = [RED, YES]
        checked_players = sheriff.knowledge.query('checked == 1')
        self.common_knowledge.update(checked_players[['color']])

    # голосование
    def election(self, candidates_id:list[int], re_election=False):
        election_list = pd.DataFrame(
            index=candidates_id, data={'voted_by': None, 'votes_recieved':0})\
            .astype({'voted_by':'object', 'votes_recieved':'Int8'})
        election_list['voted_by'] = [[] for _ in range(len(candidates_id))]
        if re_election:
            self.log(event='reelection', candidates=candidates_id)
        else:
            self.log(event='declare_election', players=candidates_id)
        voters = self.get_players(alive=YES)
        for p in voters:
            target_id = p.vote(candidates_id)
            target = self.players[target_id]
            election_list.loc[target_id, 'voted_by'].append(p.id)
            election_list.loc[target_id, 'votes_recieved'] += 1
            target.suspect(p.id, target.rancor_rate)
        for p in election_list.query('votes_recieved > 0').iterrows():
            self.log(event='vote', players=p[1], victim=p[0])
        max_votes = election_list['votes_recieved'].max()
        leaders_id = election_list.query('votes_recieved == @max_votes').index.to_list()
        if len(leaders_id) == 1: # когда был выбран один игрок
            victim = leaders_id[0]
            self.jail_player(victim)
            self.log('leader', victim=victim)
            return [victim], True # True означает, что голосование проведено 
        else: # выбрано несколько игроков на голосовании
            self.log('share', players=leaders_id)
            if re_election:
                self.log('mass', players=leaders_id)
                if random.random() > 0.5: # пока заглушка - поднять или оставить 50/50
                    for l in leaders_id:
                        self.kill_player(l)
                    self.log('lift', players=leaders_id)
                    return leaders_id, True
                else:
                    self.log('leave', players=leaders_id)
                return leaders_id, True
            else:
                return leaders_id, False

    # проверка условия победы
    def check_win(self):
        if self.get_players(color=-1, alive=1).count() >= self.get_players(
            color=1, alive=1).count():
            self.log('mafia_won')
            return -1
        elif self.get_players(color=-1, alive=1).count() == 0:
            self.log('city_won')
            return 1
        return 0
    
    def start_game(self):
        for _ in range(10):
            try:
                self.log(event='night') # ночь
                shot_target = self.hunt() # ночной отстрел
                win = self.check_win() # проверка условия победы
                if win:
                    return win
                self.don_check() # проверка дона
                self.sheriff_check() # проверка шерифа
                self.kill_player(shot_target)
                if self.players[shot_target].role == 'Sheriff':
                    self.sheriff_confess()
                self.update_players_knowledge()
                e = self.election(self.get_players(alive=1, type_result='int'))
                if not e[1]:
                    self.election(re_election=True, candidates_id=e[0])
                self.update_players_knowledge()
                win = self.check_win()
                if win:
                    return win
            except Exception:
                print(self.table)
                print(self.game_log)
                raise Exception

class GameScenario:
    ...

if __name__=='__main__':
    g1 = Game(custom_roles={'don':[1], 'sheriff':[2], 'mafia':[6, 7]})
    print(g1.table)