from dashboard.data_loader import load_data
df, _ = load_data()
print("Available columns:")
print(list(df.columns))
