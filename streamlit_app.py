import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the pre-processed data
@st.cache_data
def load_data():
    data_path = "merged_df.csv"
    merged_df = pd.read_csv(data_path)
    return merged_df

data = load_data()

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

    # Use barplot from seaborn
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
        from statsmodels.stats.weightstats import ztest
        left_lead = filtered_data[filtered_data['pitcher_hand'] == 'Left']['lead_distance']
        right_lead = filtered_data[filtered_data['pitcher_hand'] == 'Right']['lead_distance']
        
        # Check if both groups have data
        if len(left_lead) > 0 and len(right_lead) > 0:
            try:
                z_stat, pvalue = ztest(left_lead, right_lead)
                st.write(f"Z-Test P-Value: {pvalue:.4f}")
            except ZeroDivisionError:
                st.write("Error: Insufficient data for Z-Test. Please adjust your selections to include data for both pitcher hands.")
        else:
            st.write("Error: Not enough data for Z-Test. Ensure both pitcher hands have data or broaden your selection criteria.")

    if st.sidebar.button('Show ANOVA and Tukey HSD Results'):
        from scipy.stats import f_oneway
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
        
        # Ensure there is data for each pitch label
        if 'Before' in filtered_data['pitch_label'].values and 'Pickoff' in filtered_data['pitch_label'].values and 'After' in filtered_data['pitch_label'].values:
            before_list = filtered_data[filtered_data['pitch_label'] == 'Before']['lead_distance']
            pickoff_list = filtered_data[filtered_data['pitch_label'] == 'Pickoff']['lead_distance']
            after_list = filtered_data[filtered_data['pitch_label'] == 'After']['lead_distance']
            
            try:
                f_stat, pvalue = f_oneway(before_list, pickoff_list, after_list)
                st.write(f"ANOVA P-Value: {pvalue:.4f}")
                
                tukey = pairwise_tukeyhsd(endog=filtered_data['lead_distance'], groups=filtered_data['pitch_label'], alpha=0.05)
                st.write(tukey)
            except ZeroDivisionError:
                st.write("Error: Insufficient data for ANOVA test. Please adjust your selections to include sufficient data for each pitch label.")
        else:
            st.write("Error: Not enough data for ANOVA test. Ensure that each pitch label has data or broaden your selection criteria.")
