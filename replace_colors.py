import os

base_path = r"c:\Cobra\OneDrive - COBRA PERU S.A\Python\Py\Py.Anton\templates\base.html"
proy_path = r"c:\Cobra\OneDrive - COBRA PERU S.A\Python\Py\Py.Anton\templates\proyectos.html"

def replace_in_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

base_replacements = [
    ('--ios-accent: #a15bf2;', '--ios-accent: #3b82f6;'),
    ('rgba(161, 91, 242,', 'rgba(59, 130, 246,'),
    ('bg-[#a15bf2]', 'bg-blue-600'),
    ('shadow-[#4c257b]/40', 'shadow-blue-900/40'),
    ('from-[#a15bf2] to-[#7c3aed]', 'from-blue-500 to-blue-700'),
    ('>A</div>', '><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"></path></svg></div>')
]

proy_replacements = [
    ('#a15bf2', '#3b82f6'),
    ('#d194ff', '#60a5fa'),
    ('#4c257b', '#1e3a8a'),
    ('#8b45d0', '#2563eb'), 
    ('class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center hidden p-4"', 
     'class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center hidden p-4 pointer-events-auto"'),
    ('flex items-center justify-center text-white shadow-lg shadow-[#1e3a8a]/20',
     'flex items-center justify-center text-white shadow-lg shadow-[#1e3a8a]/40') # fix slightly darker shadow for logo
]

replace_in_file(base_path, base_replacements)
replace_in_file(proy_path, proy_replacements)
print("Replacements done successfully.")
