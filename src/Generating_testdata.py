import pandas as pd
import random

# Parameters
min_length = 1
max_length = 13000
min_count = 1
max_count = 50
required_total = 50000

part_ids = []
part_lengths = []
counts = []
current_total = 0
row_id = 1

while current_total < required_total:
    remaining = required_total - current_total
    if remaining > max_count:
        count = random.randint(min_count, max_count)
    else:
        count = remaining
    part_ids.append(row_id)
    part_lengths.append(random.randint(min_length, max_length))
    counts.append(count)
    current_total += count
    row_id += 1

# Build DataFrame

data = {
    'PartId': part_ids,
    'PartLength': part_lengths,
    'Count': counts
}

df = pd.DataFrame(data)

df.to_csv('./data/dummy_parts2.csv', index=False)
print('Generated dummy_parts.csv with', len(df), 'rows. Total count:', df['Count'].sum())
