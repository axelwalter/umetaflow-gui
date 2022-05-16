import pandas as pd

df = pd.read_csv('PGN_Ecoli_Bsubtilis.csv')

df['id'] = ['PGNDB' + str(i+1) for i in range(len(df['Summenformel']))]

with open('pgn_structs.tsv', 'w') as f:
    for i, name in zip(df['id'], df['Struktur']):
        f.write(f'{i}\t{name}\tSMILE\tInChI\n')

with open('pgn_maps.tsv', 'w') as f:
    f.write('database_name	PGN_Ecoli_Bsubtilis\n')
    f.write('database_version	1.0\n')
    for i, formula, name in zip(df['id'], df['Summenformel'], df['Struktur']):
        f.write(f'0\t{formula}\t{i}\n')