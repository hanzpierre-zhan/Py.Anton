import os

templates_dir = r"c:\Cobra\OneDrive - COBRA PERU S.A\Python\Py\Py.Anton\templates"

replacements = [
    ('#a15bf2', '#3b82f6'), # purple to blue-500
    ('rgba(161, 91, 242,', 'rgba(59, 130, 246,'), # rgba purple to rgba blue
    ('#d194ff', '#60a5fa'), # light purple to blue-400
    ('#4c257b', '#1e3a8a'), # dark purple to blue-900
    ('#8b45d0', '#2563eb'), # hover purple to blue-600
    ('#7c3aed', '#1d4ed8'), # gradient end purple to blue-700
]

for filename in os.listdir(templates_dir):
    if filename.endswith(".html"):
        path = os.path.join(templates_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for old, new in replacements:
            content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

print("Global replacements done.")
