import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Read the data
dete_survey = pd.read_csv('data/dete_survey.csv',na_values='Not Stated')
tafe_survey = pd.read_csv('data/tafe_survey.csv')

#Quick exploration of the data
print(dete_survey.head())
print(dete_survey.info())
print(tafe_survey.head())
print(tafe_survey.info())

# Remove columns we don't need for our analysis
dete_survey_updated=dete_survey.drop(dete_survey.columns[28:49],axis=1)
tafe_survey_updated=tafe_survey.drop(tafe_survey.columns[17:66],axis=1)

#Check that the columns were dropped
print(dete_survey_updated.columns)
print(tafe_survey_updated.columns)

# Clean the column names
dete_survey_updated.columns=dete_survey_updated.columns.str.lower().str.strip().str.replace(' ','_')

# Update column names to match the names in dete_survey_updated
tafe_survey_updated.rename(columns={'Record ID':'id','CESSATION YEAR':'cease_date','Reason for ceasing employment':'separationtype',
                                    'Gender. What is your Gender?':'gender','CurrentAge. Current Age':'age','Employment Type. Employment Type':'employment_status',
                                    'Classification. Classification': 'position','LengthofServiceOverall. Overall Length of Service at Institute (in years)': 'institute_service',
                                    'LengthofServiceCurrent. Length of Service at current workplace (in years)': 'role_service'},inplace=True)

# Check the unique values for the separationtype column
tafe_survey_updated['separationtype'].value_counts()
dete_survey_updated['separationtype'].value_counts()

# Select only the resignation separation types from each dataframe
dete_resignations=dete_survey_updated[dete_survey_updated.separationtype.str.startswith('Resignation')].copy()
tafe_resignations=tafe_survey_updated[tafe_survey_updated.separationtype == 'Resignation'].copy()

# Extract the years and convert them to a float type
dete_resignations.cease_date=dete_resignations.cease_date.str.split('/').str[-1].astype('float')

# Calculate the length of time an employee spent in their respective workplace and create a new column
dete_resignations['institute_service']=dete_resignations.cease_date-dete_resignations.dete_start_date

# Quick check of the result
dete_resignations['institute_service'].head()

# Update the values in columns related to dissatisfaction to be either True, False, or NaN
def update_vals(val):
    if pd.isnull(val):
        return np.nan
    elif val == '-':
        return False
    else:
        return True
    
   # DETE
dete_resignations['dissatisfied'] = dete_resignations[['job_dissatisfaction',
       'dissatisfaction_with_the_department', 'physical_work_environment',
       'lack_of_recognition', 'lack_of_job_security', 'work_location',
       'employment_conditions', 'work_life_balance',
       'workload']].any(axis=1, skipna=False)
dete_resignations_up = dete_resignations.copy()
dete_resignations_up['dissatisfied'].value_counts(dropna=False)

# TEFE
tafe_resignations['dissatisfied'] = tafe_resignations[['Contributing Factors. Dissatisfaction', 'Contributing Factors. Job Dissatisfaction']].map(update_vals).any(axis=1, skipna=False)
tafe_resignations_up = tafe_resignations.copy()
tafe_resignations_up['dissatisfied'].value_counts(dropna=False)

# Add an institute column
dete_resignations_up['institute'] = 'DETE'
tafe_resignations_up['institute'] = 'TAFE'

# Combine the dataframes
combined=pd.concat([dete_resignations_up,tafe_resignations_up],ignore_index=True)

# Drop columns with less than 500 non null values
combined_updated=combined.dropna(thresh=500,axis=1)

# Extract the years of service and convert the type to float
combined_updated['institute_service'] = combined_updated['institute_service'].astype('str').str.extract(r'(\d+)').astype('float')

# Convert years of service to categories
def transform_service(val):
    if val >= 11:
        return "Veteran"
    elif 7 <= val < 11:
        return "Established"
    elif 3 <= val < 7:
        return "Experienced"
    elif pd.isnull(val):
        return np.nan
    else:
        return "New"
combined_updated['service_cat'] = combined_updated['institute_service'].apply(transform_service)

# Replace missing values with the most frequent value, False
combined_updated['dissatisfied'] = combined_updated['dissatisfied'].fillna(False)

# Calculate the percentage of employees who resigned due to dissatisfaction in each category
dis_pct = combined_updated.pivot_table(index='service_cat', values='dissatisfied')

# Plot the results

order = ['New', 'Experienced', 'Established', 'Veteran']
dis_pct = dis_pct.reindex(order)
ax = dis_pct.plot(kind='bar', rot=0, legend=False, color='steelblue')
ax.set_title("Part des démissions liées à l'insatisfaction, par ancienneté")
ax.set_xlabel("Catégorie d'ancienneté")
ax.set_ylabel("Proportion")
plt.tight_layout()
plt.savefig('images/insatisfaction_par_anciennete.png', dpi=150, bbox_inches='tight')
plt.show()

# Convert age to categories
def age_cat(val):
    if pd.isnull(val): return np.nan
    elif val < 30: return "Moins de 30 ans"
    elif val < 50: return "30-49 ans"
    else: return "50 ans et plus"

combined_updated['age'] = combined_updated['age'].astype('str').str.extract(r'(\d+)').astype('float')
combined_updated['age_cat'] = combined_updated['age'].apply(age_cat)
age_pct = combined_updated.pivot_table(index='age_cat', values='dissatisfied')

# Plot the results
order = ['Moins de 30 ans', '30-49 ans', '50 ans et plus']
age_pct = age_pct.reindex(order)
ax = age_pct.plot(kind='bar', rot=0, legend=False, color='steelblue')
ax.set_title("Part des démissions liées à l'insatisfaction, par tranches d'âge")
ax.set_xlabel("Tranche d'âge")
ax.set_ylabel("Proportion")
plt.tight_layout()
plt.savefig('images/insatisfaction_par_tranche_age.png', dpi=150, bbox_inches='tight')
plt.show()
print(age_pct)
print(dis_pct)
