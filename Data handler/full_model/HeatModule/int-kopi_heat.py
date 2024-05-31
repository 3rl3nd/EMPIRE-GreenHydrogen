import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype
from scipy.interpolate import interp1d
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def interpolate_series(series, sheet):
    # Create new index with additional points
    #new_index = np.linspace(series.index.min(), series.index.max(), n)
    # Reindex the original series to match the new index
    # 'method=None' ensures that only the existing indices are filled with original values
    # The rest will remain NaN and will be interpolated later

    df = series.to_frame(name = 'value')
    df['period'] = [20, 25, 30, 35, 40, 45, 50, 55]
    #reindexed_series = series.reindex(new_index, method=None)
    new_rows = pd.DataFrame({'value': [None,None,None,None,None,None], 'period': [24,27,33,36,39,42]})
    df = pd.concat([new_rows, df])
    df = df.sort_values(by='period').reset_index(drop=True)
    # Interpolate the missing values
    df.set_index('period', inplace=True)

    
    #df['value'] = df['value'].interpolate(method='linear')
    x_known = df.dropna().index.values
    y_known = df.dropna().values.flatten()

    # Creating an interpolation function based on known values
    interp_func = interp1d(x_known, y_known, kind='linear', fill_value="extrapolate")

    # Applying the interpolation function to all index values (including those of NaN values)
    df['value'] = interp_func(df.index.values)

    df_dropped = df.drop([20,25,35,40,50,55])   #[20,25,26,29,30,32,35,38,40,41,44,45,47,50,55])

    interpolated_series = df_dropped['value'] #reindexed_series.interpolate()
  
    return interpolated_series


def create_new_df(file, sheet, columns, periods=8, current_leap=5, new_leap=3, remove_periods=5):
    header_rows = pd.read_excel(file, sheet_name=sheet, nrows=2, header=None)
    input_sheet = pd.read_excel(file, sheet, skiprows=2)
    sort_by_nodes = [('HeatModuleNode.xlsx', 'HeatAnnualDemand'),('HeatModuleNode.xlsx', 'NodeLostLoadCost'), 
                     ('HeatModuleStorage.xlsx', 'InitialPowerCapacity'), ('HeatModuleStorage.xlsx', 'EnergyInitialCapacity')
                     ]
    sort_by_node = [('HeatModuleConverter.xlsx','MaxBuildCapacity')]
    data_table = input_sheet.iloc[:, columns]
    original_column_names = data_table.columns.tolist()
    data_table.columns = pd.Series(data_table.columns).str.replace(' ', '_')

    if ((file,sheet)) in sort_by_nodes:
        print(file +':  '+sheet)
        data_table = data_table.sort_values(by="Nodes")    
    
    if ((file,sheet)) in sort_by_node:
        print(file +':  '+sheet)
        data_table = data_table.sort_values(by="Node")

    if file in change_files_dict.keys():
        if sheet not in change_files_dict[file].keys():
            return pd.read_excel(file, sheet, header=None)
    else:
        return pd.read_excel(file, sheet, header=None)

    if 'Period' not in input_sheet or input_sheet["Period"].nunique()<=1: # If period is not included or there is just one period, just skip 
        return pd.read_excel(file, sheet, header=None)
    # print("SHIT",file," FUCK: ",sheet)

    new_data = {}

    for column in data_table.columns:
        series = data_table[column]  # Access the column

        if len(series)%periods != 0:
            print('ERROR:   ' + sheet)
            print(series)
        if column == "Period":
            concatenated_series = pd.Series()  # Initialize an empty series for concatenation
            for i in range(round(len(series) / periods)):
                # Calculate the length of each segment
                #segment_length = round(periods * current_leap / new_leap - remove_periods)
                # Generate a range from 1 to segment_length
                period_range = pd.Series(range(1, new_periods+1))
                # Concatenate the generated range to the concatenated_series
                concatenated_series = pd.concat([concatenated_series, period_range], ignore_index=True)
            new_data[column] = concatenated_series

        elif is_numeric_dtype(series):  # Check if the series is numeric
            concatenated_series = pd.Series()  # Initialize an empty series for concatenation
            for i in range(round(len(series) / periods)):
                subset = series[i * periods : (i + 1) * periods]
                subset = subset.sort_index().reset_index(drop=True)
                # print(subset)                
                # Perform interpolation
                interpolated = interpolate_series(subset, sheet)

                # Concatenate the interpolated series
                concatenated_series = pd.concat([concatenated_series, interpolated], ignore_index=True)
                # print(concatenated_series)
            # Add the concatenated series to the dictionary
            new_data[column] = concatenated_series
        else:
            # Handle non-numeric columns
            non_numeric_values = []
            for i in range(round(len(series) / periods)):
                # Replicate the existing value 'periods' times
                value = series.iloc[i * periods]
                non_numeric_values.extend([value] * new_periods )    #(round(periods * current_leap / new_leap-remove_periods)))
                
                # print(non_numeric_values)
            # Add the non-numeric values to the dictionary
            new_data[column] = non_numeric_values
    # UGLY: 
    new_data_frame = pd.DataFrame(new_data)
    # print("NEW DATA\n",new_data_frame)
    expanded_header_rows = pd.concat([header_rows, pd.DataFrame(columns=new_data_frame.columns[len(header_rows.columns):])])
    column_name_frame = pd.DataFrame([original_column_names], columns=new_data_frame.columns)
    final_data_frame = pd.concat([column_name_frame, new_data_frame], ignore_index=True)
    final_data_frame.columns = range(final_data_frame.shape[1])
    final_data_frame = pd.concat([expanded_header_rows, final_data_frame], ignore_index=True)
    # print(final_data_frame)
    return final_data_frame

periods = 8
current_leap = 5
new_leap = 3
new_periods = 8


# dick2 = {"Hydrogen.xlsx":{"ReformerCapitalCost":[0,1,2,3],
#                           "ReformerPlants":[0,1]}}

# for file, sheet_dict in dick2.items():
#     with pd.ExcelWriter(file.replace(".xlsx", "") + "_edit.xlsx") as writer:
#         for sheet, columns in sheet_dict.items():
#             df = create_new_df(file, sheet, columns)
#             df.to_excel(writer, sheet_name=sheet, index=False, header=False)



file_sheet_columns_dict = {
    "HeatModuleSets.xlsx": {
        "Storage": [],
        "Generator": [],
        "Technology": [],
        "Converter": [],
        "StorageOfNodes": [0, 1],
        "ConverterOfNodes": [0, 1],
        "GeneratorsOfNode": [0, 1],
        "GeneratorsOfTechnology": [0, 1]
    },
    "HeatModuleGenerator.xlsx": {
        "FixedOMCosts": [0, 1, 2],
        "CapitalCosts": [0, 1, 2],
        "VariableOMCosts": [0, 1],
        "FuelCosts": [0, 1, 2],
        "Efficiency": [0, 1, 2],
        "RefInitialCap": [0, 1, 2],
        "ScaleFactorInitialCap": [0, 1, 2],
        "InitialCapacity": [0, 1, 2, 3],
        "MaxBuiltCapacity": [0, 1, 2, 3],
        "MaxInstalledCapacity": [0, 1, 2],
        "RampRate": [0, 1],
        "GeneratorTypeAvailability": [0, 1],
        "CO2Content": [0, 1],
        "Lifetime": [0, 1],
        "CHPEfficiency": [0, 1, 2]
    },
    "HeatModuleStorage.xlsx": {
        "StorageBleedEfficiency": [0, 1],
        "StorageChargeEff": [0, 1],
        "StorageDischargeEff": [0, 1],
        "StorageInitialEnergyLevel": [0, 1],
        "InitialPowerCapacity": [0, 1, 2, 3],
        "PowerCapitalCost": [0, 1, 2],
        "PowerFixedOMCost": [0, 1, 2],
        "PowerMaxBuiltCapacity": [0, 1, 2, 3],
        "EnergyCapitalCost": [0, 1, 2],
        "EnergyFixedOMCost": [0, 1, 2],
        "EnergyInitialCapacity": [0, 1, 2, 3],
        "EnergyMaxBuiltCapacity": [0, 1, 2, 3],
        "EnergyMaxInstalledCapacity": [0, 1, 2],
        "PowerMaxInstalledCapacity": [0, 1, 2],
        "Lifetime": [0, 1],
        "StoragePowToEnergy": [0, 1]
    },
    "HeatModuleNode.xlsx": {
        "HeatAnnualDemand": [0, 1, 2],
        "NodeLostLoadCost": [0, 1, 2],
        "ElectricHeatShare": [0, 1]
    },
    "HeatModuleConverter.xlsx": {
        "FixedOMCosts": [0, 1, 2],
        "CapitalCosts": [0, 1, 2],
        "InitialCapacity": [0, 1, 2, 3],
        "MaxBuildCapacity": [0, 1, 2, 3],
        "MaxInstallCapacity": [0, 1, 2],
        "Efficiency": [0, 1],
        "Lifetime": [0, 1]
    }
}

change_files_dict = {
    "HeatModuleGenerator.xlsx": {
        "FixedOMCosts": [0, 1, 2],
        "CapitalCosts": [0, 1, 2],
        "FuelCosts": [0, 1, 2],
        "Efficiency": [0, 1, 2],
        "ScaleFactorInitialCap": [0, 1, 2],
        "CHPEfficiency": [0, 1, 2]
    },
    "HeatModuleNode.xlsx": {
        "HeatAnnualDemand": [0, 1, 2]
    },
    "HeatModuleConverter.xlsx": {
        "FixedOMCosts": [0, 1, 2],
        "CapitalCosts": [0, 1, 2],
        "InitialCapacity": [0, 1, 2, 3]
    }
}

for file, sheet_dict in file_sheet_columns_dict.items():
    with pd.ExcelWriter('Edited/'+file,engine="xlsxwriter") as writer:
        for sheet, columns in sheet_dict.items():
            df = create_new_df(file, sheet, columns,periods=8,remove_periods=3,current_leap=5,new_leap=3)
            df.to_excel(writer, sheet_name=sheet, index=False, header=False)