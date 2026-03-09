import os

FILE_PATH = "eval/generate_txt_dataset.py"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Fix the broken newlines in the file.write statements
# Using a simple string replacement for the specific broken blocks
new_func = '''def write_cumulative_path(file, path_name, script):
    file.write(f"====================================================\\n")
    file.write(f"           PATH: {path_name} (40 INPUT TURNS)       \\n")
    file.write(f"====================================================\\n\\n")
    
    messages_so_far = []
    input_count = 1
    
    for role, content in script:
        messages_so_far.append(f"{role.upper()}: {content}")
        
        if role == "user":
            file.write(f"--- INPUT {input_count} ---\\n")
            # Write the entire cumulative history up to this point
            for msg in messages_so_far:
                file.write(msg + "\\n")
            file.write("\\n")
            input_count += 1
            
    file.write("\\n\\n")'''

# Find where the broken function starts and replace the rest of the file (except the if __name__ block)
lines = text.split('\n')
new_lines = []
in_broken_func = False
for line in lines:
    if line.startswith("def write_cumulative_path"):
        in_broken_func = True
        new_lines.append(new_func)
    elif line.startswith("if __name__ == \"__main__\":"):
        in_broken_func = False
        new_lines.append(line)
    elif not in_broken_func:
        new_lines.append(line)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write('\n'.join(new_lines))

print("Fixed syntax error!")
