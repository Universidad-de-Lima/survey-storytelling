import sys
sys.path.insert(0, '.')

with open('zoho-survey/scripts/build_json.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Calidad → Claridad de los recursos académicos
content = content.replace('"Calidad de los recursos académicos"', '"Claridad de los recursos académicos"')

# Fix 2: Ambientes y aulas → Ambientes y salas para estudio  
content = content.replace('"Ambientes y aulas para estudio"', '"Ambientes y salas para estudio"')

# Fix 3: Información sobre tu → Información sobre el récord académico
content = content.replace('"Información sobre tu récord académico"', '"Información sobre el récord académico"')

with open('zoho-survey/scripts/build_json.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed. Verifying...")
with open('zoho-survey/scripts/build_json.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if any(w in line for w in ['Ambientes', 'recursos académicos', 'récord académico']):
        print(f'  {i}: {line.rstrip()}')
