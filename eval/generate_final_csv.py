import sys
import os
import csv
import json

# Add eval director to python path to import the scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_txt_dataset import happy_script, vague_script, troll_script

DATASET_CSV = "eval/purpose_dataset.csv"

def append_to_dataset(script, dataset_list):
    messages_so_far = [] # Array that grows
    for role, content in script:
        # 1. Append the current message
        messages_so_far.append({"role": role, "content": content})
        
        # 2. IF it is a user message, we save the CURRENT state of messages_so_far into the dataset
        if role == "user":
            # We MUST use list() to create a copy of the list at this specific moment in time.
            snapshot = list(messages_so_far)
            dataset_list.append({
                "inputs.messages": json.dumps(snapshot, ensure_ascii=False)
            })

if __name__ == "__main__":
    dataset = []
    
    append_to_dataset(happy_script, dataset)
    append_to_dataset(vague_script, dataset)
    append_to_dataset(troll_script, dataset)
    
    with open(DATASET_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["inputs.messages"])
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)
    
    print(f"Generated {len(dataset)} single-column cumulative input samples in {DATASET_CSV}.")
