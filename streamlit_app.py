import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import f_oneway
from statsmodels.stats.weightstats import ztest
from statsmodels.stats.multicomp import pairwise_tukeyhsd

# Load the pre-processed data
@st.cache_data
def load_data():
    data_path = "merged_df"  # Update this path
    pitches_pickoffs_merged_df = pd.read_csv(data_path)
    return pitches_pickoffs_merged_df

@st.cache_data
def load_additional_data():
    data_path = "pitches_pickoffs_merged_df.csv"  # Update this path
    pitches_pickoffs_data = pd.read_csv(data_[path)
    return pitches_pickoffs_data

data = load_data()
additional_data = load_additional_data()

# Custom function to calculate means by split
def means_by_split(merged_df):
    means = pd.DataFrame()
    before_left_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Left') & (merged_df['pitch_label'] == 'before'), 'lead_distance']
    pickoff_left_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Left') & (merged_df['pitch_label'] == 'pickoff'), 'lead_distance']
    after_left_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Left') & (merged_df['pitch_label'] == 'after'), 'lead_distance']
    before_right_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Right') & (merged_df['pitch_label'] == 'before'), 'lead_distance']
    pickoff_right_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Right') & (merged_df['pitch_label'] == 'pickoff'), 'lead_distance']
    after_right_col = merged_df.loc[(merged_df['pitcher_hand'] == 'Right') & (merged_df['pitch_label'] == 'after'), 'lead_distance']
    
    # Assign to means dataframe
    means.loc['Before', 'Left'] = before_left_col.mean()
    means.loc['Pickoff', 'Left'] = pickoff_left_col.mean()
    means.loc['After', 'Left'] = after_left_col.mean()
    means.loc['Before', 'Right'] = before_right_col.mean()
    means.loc['Pickoff', 'Right'] = pickoff_right_col.mean()
    means.loc['After', 'Right'] = after_right_col.mean()
    return means

# Statistical Tests Functions
def ztest_by_hand(pitches_pickoffs_merged_df):
    pitches_merged_df = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['event_code'] == 1]  # just want pitches, not pickoffs
    left_lead = pitches_merged_df.loc[pitches_merged_df['pitcher_hand'] == 'Left']['lead_distance']
    right_lead = pitches_merged_df.loc[pitches_merged_df['pitcher_hand'] == 'Right']['lead_distance']
    z_stat, pvalue = ztest(list(left_lead), list(right_lead), value=0)
    return z_stat, pvalue

def anova_and_posthoc_trio(pickoffs_merged_df_trios):
    before_list = list(pickoffs_merged_df_trios.loc[pickoffs_merged_df_trios['pitch_label'] == 'before']['lead_distance'])
    pickoff_list = list(pickoffs_merged_df_trios.loc[pickoffs_merged_df_trios['pitch_label'] == 'pickoff']['lead_distance'])
    after_list = list(pickoffs_merged_df_trios.loc[pickoffs_merged_df_trios['pitch_label'] == 'after']['lead_distance'])
    f_stat, pvalue = f_oneway(before_list, pickoff_list, after_list)
    tukey = pairwise_tukeyhsd(endog=pickoffs_merged_df_trios['lead_distance'], groups=pickoffs_merged_df_trios['pitch_label'], alpha=.05)
    return f_stat, pvalue, tukey

def anova_and_posthoc_levels(pitches_pickoffs_merged_df):
    pitches_merged_df = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['event_code'] == 1]
    a_column = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['HomeTeam'] == 'Home1A']['lead_distance']
    aa_column = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['HomeTeam'] == 'Home2A']['lead_distance']
    aaa_column = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['HomeTeam'] == 'Home3A']['lead_distance']
    aaaa_column = pitches_pickoffs_merged_df.loc[pitches_pickoffs_merged_df['HomeTeam'] == 'Home4A']['lead_distance']
    means = pd.DataFrame()
    means.loc['A', 'Mean'] = a_column.mean()
    means.loc['AA', 'Mean'] = aa_column.mean()
    means.loc['AAA', 'Mean'] = aaa_column.mean()
    means.loc['AAAA', 'Mean'] = aaaa_column.mean()
    f_stat, pvalue = f_oneway(a_column, aa_column, aaa_column, aaaa_column)
    tukey = pairwise_tukeyhsd(endog=pitches_pickoffs_merged_df['lead_distance'], groups=pitches_pickoffs_merged_df['HomeTeam'], alpha=.05)
    return f_stat, pvalue, tukey

# Streamlit app layout
st.title("Holding 'Em Close: \nAn Interactive Bar Chart Analyzing Pickoff Attempts")

# Sidebar filters
leagues = data['HomeTeam'].unique().tolist()
leagues.insert(0, 'All Leagues')  # Add 'All Leagues' at the top

selected_league = st.sidebar.selectbox('Select League', leagues)
selected_hands = st.sidebar.multiselect('Select Pitcher Handedness', ['Left', 'Right'], default=['Left', 'Right'])

# Filter data based on selections
if selected_league == 'All Leagues':
    filtered_data = data
else:
    filtered_data = data[data['HomeTeam'] == selected_league]

if selected_hands:
    filtered_data = filtered_data[filtered_data['pitcher_hand'].isin(selected_hands)]

# Check for sufficient data
if filtered_data.empty:
    st.write("No data available for the selected filters. Please adjust your selections.")
else:
    # Calculate averages using means_by_split
    average_lead_distances = means_by_split(filtered_data).reset_index().melt(id_vars='index')
    average_lead_distances.columns = ['pitch_label', 'pitcher_hand', 'lead_distance']
    average_lead_distances['HomeTeam'] = selected_league if selected_league != 'All Leagues' else 'All Leagues'

    # Ensure the order of the pitch labels
    average_lead_distances['pitch_label'] = pd.Categorical(average_lead_distances['pitch_label'], categories=['Before', 'Pickoff', 'After'], ordered=True)
    average_lead_distances = average_lead_distances.sort_values('pitch_label')

    # Plotting
    fig, ax = plt.subplots(figsize=(10, 6))

    # Use barplot from seaborn with custom colors
    sns.barplot(x='pitch_label', y='lead_distance', hue='pitcher_hand', data=average_lead_distances, ax=ax, palette=['red', 'blue'])

    # Add data labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', label_type='edge', padding=3, fontsize=10)

    ax.set_title('Average Lead Distances')
    ax.set_xlabel('Pitch Label')
    ax.set_ylabel('Lead Distance (ft)')

    # Adjust layout to ensure labels are not cut off
    plt.tight_layout()

    st.pyplot(fig)

    # Additional information
    if st.sidebar.button('Show Z-Test Results'):
        z_stat, pvalue = ztest_by_hand(additional_data)
        st.write(f"Z-Test P-Value: {pvalue:.4f}")

    if st.sidebar.button('Show ANOVA and Tukey HSD Results'):
        f_stat, pvalue, tukey = anova_and_posthoc_trio(additional_data)
        st.write(f"ANOVA P-Value: {pvalue:.4f}")
        st.write("Tukey HSD Test Results:")
        st.write(tukey)
