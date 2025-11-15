import sqlite3

conn = sqlite3.connect('data/list_sync.db')
cursor = conn.cursor()

# Get sample records
cursor.execute('SELECT id, title, media_type, imdb_id, tmdb_id, overseerr_id FROM synced_items LIMIT 10')
rows = cursor.fetchall()

print('Sample Database Records:')
print('=' * 120)
print(f"{'ID':<5} | {'Title':<40} | {'Type':<6} | {'IMDB ID':<12} | {'TMDB ID':<10} | {'Overseerr ID':<12}")
print('-' * 120)

for row in rows:
    title = (row[1][:37] + '...') if row[1] and len(row[1]) > 40 else (row[1] or 'N/A')
    print(f"{row[0]:<5} | {title:<40} | {row[2]:<6} | {row[3] or 'N/A':<12} | {row[4] or 'N/A':<10} | {row[5] or 'N/A':<12}")

conn.close()

