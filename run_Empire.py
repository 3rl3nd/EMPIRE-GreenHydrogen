from reader import generate_tab_files
from Empire import run_empire
from scenario_random import generate_random_scenario
from datetime import datetime
import time
import gc
import os


########
##USER##
########

short = True

USE_TEMP_DIR = True #True/False
temp_dir = '/mnt/beegfs/users/erlenhor'
version = 'full_model_interpolated-cap_update'
NoOfPeriods = 8

NoOfScenarios = 3
NoOfRegSeason = 4
lengthRegSeason = 7*24
regular_seasons = ["winter", "spring", "summer", "fall"]
NoOfPeakSeason = 2
lengthPeakSeason = 24
discountrate = 0.05
WACC = 0.05
LeapYearsInvestment = 3
solver = "Gurobi" #"Gurobi" #"CPLEX" #"Xpress"

#If using fixed sample set scenariogeneration to False and FIX_SAMPLE to True
scenariogeneration = True
FIX_SAMPLE = False

WRITE_LP = False
PICKLE_INSTANCE = False
hydrogen=True
FLEX_IND = True
Reformer_H2 = False

#Turning Green Hydrogen module to True and ensuring all hydrogen from electrolysis is Green
GREEN_H2 = True
ONLY_GREEN = True

#Green hydrogen rules
ADDITIVITY_GH2= True

SPATIAL_AND_TEMPORAL_GH2= True
ONLY_TEMPORAL_GH2= False
ONLY_SPATIAL_GH2= False

RENEWABLE_GRID_RUlE = True


GREEN_PROD_REQUIREMENT=[10400314.24,
                        9930975.897,
                        10391961.73,
                        10842315.99,
                        11420501.49,
                        12338284.93,
                        14864796.39,
                        14846592.11]

GREEN_PROD_REQUIREMENT= [0,0,0,0,0,0,0,0]

if short:
    NoOfPeriods = 2
    version = 'short_model'
    scenariogeneration = True
    GREEN_PROD_REQUIREMENT= [20,0,0,0,0,0,0,0]



def get_unique_filename(base_path, filename):
    """
    Generates a unique filename. If the given filename already exists, it appends a number to the filename.

    :param base_path: The directory in which to check for the file.
    :param filename: The desired filename.
    :return: A unique filename.
    """
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(base_path, unique_filename)):
        unique_filename = f"{filename}_{counter}"
        counter += 1
    return base_path + unique_filename

#######
##RUN##
#######
if FLEX_IND is True:
    ind_str = 'flexible_industry'
else:
    ind_str = 'inflexible_industry'

if GREEN_H2 is True:
    green_str = 'green_H2'
else:
    green_str = 'no_green_H2' 

name = f'green_prod_tot'
if short:
    name = f'short'
workbook_path = 'Data handler/' + version
tab_file_path = 'Data handler/' + version + '/Tab_Files_' + name
scenario_data_path = 'Data handler/' + version + '/ScenarioData'
result_file_path = get_unique_filename('Results/',name)
FirstHoursOfRegSeason = [lengthRegSeason*i + 1 for i in range(NoOfRegSeason)]
FirstHoursOfPeakSeason = [lengthRegSeason*NoOfRegSeason + lengthPeakSeason*i + 1 for i in range(NoOfPeakSeason)]
Period = [i + 1 for i in range(NoOfPeriods)]
Scenario = ["scenario"+str(i + 1) for i in range(NoOfScenarios)]
peak_seasons = ['peak'+str(i + 1) for i in range(NoOfPeakSeason)]
Season = regular_seasons + peak_seasons
Operationalhour = [i + 1 for i in range(FirstHoursOfPeakSeason[-1] + lengthPeakSeason - 1)]
HoursOfRegSeason = [(s,h) for s in regular_seasons for h in Operationalhour \
                 if h in list(range(regular_seasons.index(s)*lengthRegSeason+1,
                               regular_seasons.index(s)*lengthRegSeason+lengthRegSeason+1))]
HoursOfPeakSeason = [(s,h) for s in peak_seasons for h in Operationalhour \
                     if h in list(range(lengthRegSeason*len(regular_seasons)+ \
                                        peak_seasons.index(s)*lengthPeakSeason+1,
                                        lengthRegSeason*len(regular_seasons)+ \
                                            peak_seasons.index(s)*lengthPeakSeason+ \
                                                lengthPeakSeason+1))]
HoursOfSeason = HoursOfRegSeason + HoursOfPeakSeason
dict_countries = {"AT": "Austria", "BA": "BosniaH", "BE": "Belgium",
                  "BG": "Bulgaria", "CH": "Switzerland", "CZ": "CzechR",
                  "DE": "Germany", "DK": "Denmark", "EE": "Estonia",
                  "ES": "Spain", "FI": "Finland", "FR": "France",
                  "GB": "GreatBrit.", "GR": "Greece", "HR": "Croatia",
                  "HU": "Hungary", "IE": "Ireland", "IT": "Italy",
                  "LT": "Lithuania", "LU": "Luxemb.", "LV": "Latvia",
                  "MK": "Macedonia", "NL": "Netherlands", "NO": "Norway",
                  "PL": "Poland", "PT": "Portugal", "RO": "Romania",
                  "RS": "Serbia", "SE": "Sweden", "SI": "Slovenia",
                  "SK": "Slovakia", "MF": "MorayFirth", "FF": "FirthofForth",
                  "DB": "DoggerBank", "HS": "Hornsea", "OD": "OuterDowsing",
                  "NF": "Norfolk", "EA": "EastAnglia", "BS": "Borssele",
                  "HK": "HollandseeKust", "HB": "HelgoländerBucht", "NS": "Nordsøen",
                  "UN": "UtsiraNord", "SN1": "SørligeNordsjøI", "SN2": "SørligeNordsjøII",
                  "EHGB":"Energyhub Great Britain", "EHNO": "Energyhub Norway",
                  "EHEU": "Energyhub EU"}
offshoreNodesList = ["Energyhub Great Britain", "Energyhub Norway", "Energyhub EU"]
windfarmNodes = ["Moray Firth","Firth of Forth","Dogger Bank","Hornsea","Outer Dowsing","Norfolk","East Anglia","Borssele","Hollandsee Kust","Helgoländer Bucht","Nordsøen","Utsira Nord","Sørlige Nordsjø I","Sørlige Nordsjø II"]

if short: 
    dict_countries = {"DK": "Denmark",
                  "GB": "GreatBrit.","NL": "Netherlands"}
    offshoreNodesList = ["Energyhub Great Britain", "Energyhub Norway", "Energyhub EU"]
    windfarmNodes = ["Moray Firth","Firth of Forth","Dogger Bank","Hornsea","Outer Dowsing","Norfolk","East Anglia","Borssele","Hollandsee Kust","Helgoländer Bucht","Nordsøen","Utsira Nord","Sørlige Nordsjø I","Sørlige Nordsjø II"]

    windfarmNodes = None


include_results = [
                    'results_transport_hydrogen_operations',
                    'results_hydrogen_use',
                    'results_output_transmission',
                    'results_output_gen',
                    'results_output_curtailed_prod',
                    'results_natural_gas_storage',
                    'results_industry_steel_investments',
                    'results_output_offshoreConverter',
                    'results_natural_gas_hydrogen',
                    'results_CO2_pipeline_investments',
                    'results_CO2_sequestration_operational',
                    'results_CO2_pipeline_operational',
                    'results_output_gen_tr',
                    'results_natural_gas_power',
                    'results_output_gen_el',
                    'results_objective',
                    'results_CO2_sequestration_investments',
                    'results_output_stor',
                    'results_hydrogen_storage_investments',
                    'results_industry_cement_investments',
                    'results_natural_gas_transmission',
                    'results_hydrogen_production_investments',
                    'results_natural_gas_production',
                    'results_industry_ammonia_investments',
                    'results_output_OperationalEL',
                    'results_industry_steel_production',
                    'results_hydrogen_storage_operational',
                    'results_output_conv',
                    'results_natural_gas_balance',
                    'results_output_transmission_operational',
                    'results_transport_naturalGas_operations',
                    'time_usage',
                    'results_hydrogen_production',
                    'results_hydrogen_reformer_detailed_investments',
                    'results_output_OperationalTR',
                    'results_industry_ammonia_production',
                    'results_CO2_flow_balance',
                    'results_industry_cement_production',
                    'results_output_Operational',
                    'results_output_EuropeSummary',
                    'results_hydrogen_pipeline_investments',
                    'numerics_info',
                    'results_industry_oil_production',
                    'results_transport_electricity_operations',
                    'results_power_balance',
                    'results_hydrogen_pipeline_operational'
                    ]





print('++++++++')
print('+EMPIRE+')
print('++++++++')
print('Solver: ' + solver)
print('Scenario Generation: ' + str(scenariogeneration))
print('++++++++')
print('ID: ' + name)
print('++++++++')
print('Hydrogen: ' + str(hydrogen))
print('Heat module: ' + str(HEATMODULE))
print('Green Hydrogen module: ' + str(GREEN_H2))
print('Short: ' + str(short))
print('++++++++')


if scenariogeneration:
    tick = time.time()
    generate_random_scenario(filepath = scenario_data_path,
                             tab_file_path = tab_file_path,
                             scenarios = NoOfScenarios,
                             seasons = regular_seasons,
                             Periods = NoOfPeriods,
                             regularSeasonHours = lengthRegSeason,
                             peakSeasonHours = lengthPeakSeason,
                             dict_countries = dict_countries,
                             HEATMODULE=HEATMODULE,
                             fix_sample=FIX_SAMPLE)
    tock = time.time()
    print("{hour}:{minute}:{second}: Scenario generation took [sec]:".format(
    hour=datetime.now().strftime("%H"), minute=datetime.now().strftime("%M"), second=datetime.now().strftime("%S")) + str(tock - tick))

generate_tab_files(filepath = workbook_path, tab_file_path = tab_file_path,
                   HEATMODULE=HEATMODULE, hydrogen = hydrogen, GREEN_H2=GREEN_H2, RENEWABLE_GRID_RUlE=RENEWABLE_GRID_RUlE)

run_empire(name = name,
           tab_file_path = tab_file_path,
           result_file_path = result_file_path,
           scenariogeneration = scenariogeneration,
           scenario_data_path = scenario_data_path,
           solver = solver,
           temp_dir = temp_dir,
           FirstHoursOfRegSeason = FirstHoursOfRegSeason,
           FirstHoursOfPeakSeason = FirstHoursOfPeakSeason,
           lengthRegSeason = lengthRegSeason,
           lengthPeakSeason = lengthPeakSeason,
           Period = Period,
           Operationalhour = Operationalhour,
           Scenario = Scenario,
           Season = Season,
           HoursOfSeason = HoursOfSeason,
           NoOfRegSeason=NoOfRegSeason,
           NoOfPeakSeason=NoOfPeakSeason,
           discountrate = discountrate,
           WACC = WACC,
           LeapYearsInvestment = LeapYearsInvestment,
           WRITE_LP = WRITE_LP,
           PICKLE_INSTANCE = PICKLE_INSTANCE,
           EMISSION_CAP = EMISSION_CAP,
           USE_TEMP_DIR = USE_TEMP_DIR,
           offshoreNodesList = offshoreNodesList,
           hydrogen = hydrogen,
           windfarmNodes = windfarmNodes,
           HEATMODULE=HEATMODULE,
           FLEX_IND=FLEX_IND,
           Reformer_H2=Reformer_H2,
           GREEN_H2=GREEN_H2,
           ONLY_GREEN=ONLY_GREEN,
           include_results = include_results,
            repurposeCostFactor=0.25, 
            repurposeEnergyFlowFactor=0.8,
           RussianGasCapacityFactor=0, 
            SPATIAL_AND_TEMPORAL_GH2=SPATIAL_AND_TEMPORAL_GH2, 
            ADDITIVITY_GH2=ADDITIVITY_GH2, 
            ONLY_TEMPORAL_GH2=ONLY_TEMPORAL_GH2, 
            ONLY_SPATIAL_GH2=ONLY_SPATIAL_GH2,
            start_year=2021,
            GREEN_PROD_REQUIREMENT=GREEN_PROD_REQUIREMENT,
            RENEWABLE_GRID_RUlE = RENEWABLE_GRID_RUlE
            )
gc.collect()