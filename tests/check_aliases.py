import duckdb, unicodedata, re

def normalize_text(s):
    if not s: return ''
    s = str(s).lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return s.strip()

COMUNA_ALIASES = {
    'santiago': 'santiago centro',
    'estacion central': 'estacion central',
    'la calera': 'calera',
    'trehuaco': 'treguaco',
    'marchigue': 'marchihue',
    'las guaitecas': 'guaitecas',
    'o higgins': 'ohiggins',
    'til til': 'tiltil',
    'san vicente de tagua tagua': 'san vicente',
    'paihuano': 'paiguano',
    'coyhaique': 'coihaique',
    'puerto natales': 'natales',
    'torres del payne': 'torres del paine',
    'alto bio bio': 'alto biobio',
    'chol chol': 'cholchol',
    'puerto saavedra': 'saavedra',
    'llayllay': 'llaillay',
    'llay llay': 'llaillay',
    'vichuquen': 'vichuquen',
    'navarino': 'cabo de hornos',
    'puerto williams': 'cabo de hornos'
}

con = duckdb.connect()
comunas = con.execute("SELECT distinct comuna_comprador FROM read_parquet('data/catastro_ti_saneado.parquet')").fetchall()
mapped = {}
for c in comunas:
    name = c[0]
    norm = normalize_text(name)
    resolved = COMUNA_ALIASES.get(norm, norm)
    mapped.setdefault(resolved, []).append(name)

duplicates = {k: v for k, v in mapped.items() if len(v) > 1}
print('Resolved keys with multiple raw names in parquet:')
for k, v in duplicates.items():
    print(f'  {k}: {v}')
