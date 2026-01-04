import yaml

with open('custom_game.yaml') as f:
    y = yaml.safe_load(f)

print(y)