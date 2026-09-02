import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if '{/* KOCHI MAP & WARD TABLE */}' in lines[i]:
        # we found it. Let's move it UP by one line!
        # The line before it should be '            </div>\n'
        if '</div>' in lines[i-1]:
            # swap!
            # wait, the map block is large.
            # let's find the end of the map block.
            end_map = i
            for j in range(i, len(lines)):
                if '          {/* Right Column (Span 4) */}' in lines[j]:
                    end_map = j
                    break
            
            # The div that closes the col-span-8 is at i-1.
            # we want to put that closing div at the END of the map block (before Right Column).
            closing_div = lines[i-1]
            
            # remove closing div from i-1
            lines.pop(i-1)
            # insert it at end_map - 1
            lines.insert(end_map - 1, closing_div)
            
            with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print('Fixed!')
            break
