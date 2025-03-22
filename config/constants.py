# ESPN API constants
API_ENDPOINTS = {
    'league': 'https://fantasy.espn.com/apis/v3/games/flb/seasons/{year}/segments/0/leagues/{league_id}',
    'players': 'https://fantasy.espn.com/apis/v3/games/flb/seasons/{year}/players',
}

# Baseball stat categories
BATTING_CATEGORIES = {
    0: 'AB',
    1: 'H',
    2: '2B',
    3: '3B',
    4: 'HR',
    5: 'R',
    6: 'RBI',
    7: 'SB',
    8: 'CS',
    9: 'BB',
    10: 'SO',
    11: 'AVG',
    12: 'OBP',
    13: 'SLG',
    14: 'OPS',
}

PITCHING_CATEGORIES = {
    15: 'IP',
    16: 'H',
    17: 'ER',
    18: 'BB',
    19: 'SO',
    20: 'W',
    21: 'L',
    22: 'SV',
    23: 'HLD',
    24: 'ERA',
    25: 'WHIP',
    26: 'K/9',
}

# Player positions
PLAYER_POSITIONS = {
    0: 'C',
    1: '1B',
    2: '2B',
    3: '3B',
    4: 'SS',
    5: 'OF',
    6: '2B/SS',
    7: '1B/3B',
    8: 'LF',
    9: 'CF',
    10: 'RF',
    11: 'DH',
    12: 'SP',
    13: 'RP',
    14: 'P',
}