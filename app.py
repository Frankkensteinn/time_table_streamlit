import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt

# Load the Excel file
@st.cache_data
def load_data():
    df = pd.read_excel('2024-25_class_timetable_20240830.xlsx')
    return df

# Function to calculate weekday
def calculate_output(row):
    inputs = [row['MON'], row['TUE'], row['WED'], row['THU'], row['FRI'], row['SAT'], row['SUN']]
    non_nan_index = next((i for i, x in enumerate(inputs) if not pd.isna(x)), None)
    return None if non_nan_index is None else non_nan_index + 1

# Function to determine the term
def determine_term(s):
    if 'Sem 1' in s:
        return 1
    elif 'Sem 2' in s:
        return 2
    else:
        return 3

# Main function to filter and plot timetable
def get_timetable(course_codes, selected_term):
    df = load_data()
    df.columns = df.columns.str.strip()
    
    df['weekday'] = df.apply(calculate_output, axis=1)
    df = df[~df['weekday'].isna()]
    df['weekday'] = df['weekday'].astype(int)
    
    df['term'] = df['TERM'].apply(determine_term)
    
    desired = ['term', 'COURSE CODE', 'COURSE TITLE', 'CLASS SECTION', 'weekday', 'START TIME', 'END TIME', 'VENUE']
    df = df[desired].drop_duplicates().reset_index(drop=True)

    # Filter by course codes and selected term
    filtered_df = df[df['COURSE CODE'].isin(course_codes) & (df['term'] == selected_term)].sort_values(by=['term', 'weekday', 'START TIME'])
    
    return filtered_df

# Function to plot timetable with unique colors for each (course_code, class_section)
def plot_timetable(filtered_df):
    filtered_df['start_minutes'] = filtered_df['START TIME'].apply(lambda x: (x.hour - 9) * 60 + x.minute)
    filtered_df['end_minutes'] = filtered_df['END TIME'].apply(lambda x: (x.hour - 9) * 60 + x.minute)
    
    plt.figure(figsize=(12, 8))
    
    # Create a unique identifier for each (course_code, class_section) combination
    filtered_df['unique_id'] = filtered_df['COURSE CODE'] + "_" + filtered_df['CLASS SECTION']
    unique_ids = filtered_df['unique_id'].unique()
    
    # Generate colors
    colors = cm.get_cmap('tab10', len(unique_ids))  # Choose a colormap

    for idx, unique_id in enumerate(unique_ids):
        course_rows = filtered_df[filtered_df['unique_id'] == unique_id]
        course_code, class_section = unique_id.split("_")
        
        for index, row in course_rows.iterrows():
            plt.bar(row['weekday'], row['end_minutes'] - row['start_minutes'],
                    bottom=row['start_minutes'], color=colors(idx), label=f"{course_code} {class_section}" if idx == 0 else "")
            
            plt.text(row['weekday'], row['start_minutes'] + (row['end_minutes'] - row['start_minutes']) / 2,
                     f"{course_code} {class_section}\n{row['VENUE']}\n{row['START TIME'].strftime('%H:%M')} - {row['END TIME'].strftime('%H:%M')}",
                     ha='center', va='center', color='white', fontsize=9, fontweight='bold')

    plt.xticks(ticks=[1, 2, 3, 4, 5], labels=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    plt.yticks(ticks=range(0, 600, 60), labels=[f"{h}:00" for h in range(9, 19)])
    
    plt.xlim(0.5, 5.5)
    plt.ylim(0, 600-60)
    plt.gca().invert_yaxis()
    plt.title('Class Timetable')
    plt.xlabel('Weekday')
    plt.ylabel('Time (from 9 AM)')
    
    plt.grid(False)
    plt.tight_layout()
    st.pyplot(plt)
    return plt

# Streamlit UI
st.title('Class Timetable Generator')

course_input = st.text_area('Enter Course Codes (comma-separated)', 'COMP3251, STAT4609, STAT3655')
course_codes = [code.strip() for code in course_input.split(',')]

# Term selection
term_options = [2, 1, 3]
selected_term = st.selectbox('Select Term:', term_options)

if st.button('Get Timetable'):
    filtered_df = get_timetable(course_codes, selected_term)
    if not filtered_df.empty:
        st.write(filtered_df)
        pltt = plot_timetable(filtered_df)
        if st.button('Download Timetable'):
            pltt.savefig('timetable.png')
            st.success('Timetable downloaded successfully.')
    else:
        st.warning('No classes found for the entered course codes and selected term.')