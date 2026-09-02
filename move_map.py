import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

map_start = -1
map_end = -1
for i, line in enumerate(lines):
    if '{/* KOCHI MAP & WARD TABLE */}' in line:
        map_start = i
        # find the end of the map block by finding </main>
        # wait, the map block is currently at the end of the grid.
        # it is enclosed in <div className="col-span-12 ..."> ... </div>
        # and ends right before </div> </div> </main>
        break

if map_start != -1:
    # let's find where it ends
    # The map block currently ends near the very end of the file.
    # It is right before:
    #       </div>
    #     </div>
    #   </main>
    # </div>
    # );
    
    for i in range(map_start, len(lines)):
        if '          </div>' in lines[i] and '        </div>' in lines[i+1] and '      </main>' in lines[i+2]:
            map_end = i
            break
            
    if map_end != -1:
        map_block = lines[map_start:map_end]
        # Remove col-span-12
        for i, l in enumerate(map_block):
            if 'col-span-12' in l:
                map_block[i] = l.replace('col-span-12 ', '')
            if 'h-48' in l:
                # Expand the map height to h-96 for proportional UI
                map_block[i] = l.replace('h-48', 'h-96')
            if 'max-h-64' in l:
                # Expand the table max-height
                map_block[i] = l.replace('max-h-64', 'max-h-96')

        # Find where to insert it: after BOTTOM DIAGRAM, before Right Column
        insert_idx = -1
        for i in range(len(lines)):
            if '{/* Right Column (Span 4) */}' in lines[i]:
                insert_idx = i - 1 # One div before Right Column is the closing div of Left Column
                break
                
        if insert_idx != -1:
            # We must remove map_block from its old location first, but wait, map_block is AT THE END.
            # So if we extract it, the indices change.
            new_lines = lines[:map_start] + lines[map_end:]
            
            # Now find insert_idx in the NEW lines
            insert_idx = -1
            for i in range(len(new_lines)):
                if '{/* Right Column (Span 4) */}' in new_lines[i]:
                    insert_idx = i - 1
                    break
                    
            if insert_idx != -1:
                final_lines = new_lines[:insert_idx] + map_block + new_lines[insert_idx:]
                with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
                    f.writelines(final_lines)
                print("Success")
            else:
                print("Failed to find insert index")
        else:
            print("Failed to find initial insert index")
    else:
        print("Failed to find map end")
else:
    print("Failed to find map start")
