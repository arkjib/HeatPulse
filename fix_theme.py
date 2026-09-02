with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    line = lines[i]
    
    # 1. Background colors (global replace is fine)
    line = line.replace('bg-[#070b14]', 'bg-[#110000]')
    line = line.replace('bg-[#121827]', 'bg-[#1a0505]')
    line = line.replace('bg-[#0a0f1c]', 'bg-[#110000]')
    
    # Skip risk functions entirely!
    if 'getRiskColor' in line or 'getRiskBg' in line or 'COLD_STRESS' in line or 'alertColorClass =' in line or 'alertBgClass =' in line:
        lines[i] = line
        continue
        
    if 'text-green-500' in line and 'alert' in line:
        pass # Skip alert colors logic
        
    # Replacements for UI accents
    line = line.replace('text-green-400', 'text-[#ad0007]')
    line = line.replace('text-green-300', 'text-red-400')
    line = line.replace('bg-green-500', 'bg-[#a80000]')
    line = line.replace('bg-green-400', 'bg-[#ad0007]')
    line = line.replace('border-green-500', 'border-[#a80000]')
    line = line.replace('text-emerald-400', 'text-[#ad0007]')
    line = line.replace('bg-emerald-400', 'bg-[#ad0007]')
    line = line.replace('text-emerald-500/70', 'text-red-500/70')
    line = line.replace('#4ade80', '#ad0007')
    line = line.replace('🌿', '🔥')
    
    # Fix safe states that shouldn't have been replaced if they were caught?
    # I skipped risk functions so we should be mostly fine.
    
    lines[i] = line

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Theme replaced.')
