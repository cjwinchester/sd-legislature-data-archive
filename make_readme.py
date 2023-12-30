import glob
from datetime import date


today = date.today().strftime('%B %d, %Y')

with open('README-TEMPLATE.md', 'r') as infile:
    tmpl = infile.read().splitlines()

count_sessions = len(glob.glob('data/sessions/*.json'))
count_bills = len(glob.glob('data/bills/*.json'))

# don't count the historical file
count_legislators = len(glob.glob('data/legislators/*.json')) - 1 
count_committees = len(glob.glob('data/committees/*.json'))

replacements = (
    ('{% updated %}', today),
    ('{% count_sessions %}', f'{count_sessions:,}'),
    ('{% count_legislators %}', f'{count_legislators:,}'),
    ('{% count_committees %}', f'{count_committees:,}'),
    ('{% count_bills %}', f'{count_bills:,}')
)

new_file = []
for line in tmpl:
    for repl in replacements:
        line = line.replace(*repl)
    new_file.append(line)

with open('README.md', 'w') as outfile:
    outfile.write('\n'.join(new_file))
