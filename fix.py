import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the indices
map_start = -1
right_col_start = -1
grid_end = -1

for i, line in enumerate(lines):
    if '{/* KOCHI MAP & WARD TABLE */}' in line:
        map_start = i
    if '{/* Right Column (Span 4) */}' in line:
        right_col_start = i
    if '</main>' in line:
        # grid end is two divs before </main>
        grid_end = i - 2

if map_start != -1 and right_col_start != -1:
    map_block = lines[map_start:right_col_start]
    
    # modify the div to have col-span-12
    for i, line in enumerate(map_block):
        if 'className="bg-[#121827]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-6"' in line:
            map_block[i] = line.replace('className="', 'className="col-span-12 ')
            break
            
    # remove the map block from its original position
    new_lines = lines[:map_start] + lines[right_col_start:grid_end] + map_block + lines[grid_end:]
    
    with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Success")
else:
    print("Failed to find boundaries")
