# Run Robustness Eval
from connect import *
import csv

# find out how to stub get_current so that this auto corrects cause :(
patient = get_current("Patient")
case = get_current("Case")

# clean up into objects

plan_name = "elena_test"
ct_ref_name = "Average CT"
phases_group_name = "Phases"
setup_error = 0.7  # mm
range_error = 3  # %
Dprescription = 70
n_fractions = 25

# other (thanks :( as in white walkers??????) parameters
isotropic_pos_uncertainty = False
nb_density_discretization_points = 2


###############################################################################

######### FUNCTIONS #########

#def get_relative_volume_roi_geometries(patient_model, name, goal_volume=0.05):
    #abs_vol = patient_model.RoiGeometries[name].GetRoiVolume()
    #relative_volume = float((goal_volume * 100) / abs_vol)
    #return relative_volume

def get_relative_volume_roi_geometries(eval_setup, dose, name, goal_volume = 0.05):
    
    eval_setup.AddClinicalGoal(RoiName= name, GoalCriteria="AtLeast", GoalType="AbsoluteVolumeAtDose", AcceptanceLevel=0, ParameterValue=0, IsComparativeGoal=False, Priority=2147483647)
    index = eval_setup.EvaluationFunctions.Count - 1
    abs_volume = eval_setup.EvaluationFunctions[index].GetClinicalGoalValueForEvaluationDose(DoseDistribution=dose,ScaleFractionDoseToBeamSet=False)
    eval_setup.DeleteClinicalGoal(FunctionToRemove = eval_setup.EvaluationFunctions[index])
    relative_volume = float((goal_volume * 100) / abs_volume)
    return relative_volume

def get_key(value):
    return value['label'] + '_' + value['metric']


def get_dose_statistic(dose, roi_name, dose_type):
    return dose.GetDoseStatistic(RoiName=roi_name, DoseType=dose_type) * 0.01


def get_dose_at_relative_volume(dose, roi_name, relative_volume):
    return float(
        dose.GetDoseAtRelativeVolumes(RoiName=roi_name,
                                      RelativeVolumes=[relative_volume])[0]) * 0.01

def get_relative_volume_at_dose_value(dose, roi_name, dose_value):
    return float(
        dose.GetRelativeVolumeAtDoseValues(RoiName=roi_name,
                                      DoseValues=[dose_value*100])[0]*100)  #dose value feed in cGy   returns relative volume in % 

def worst_dose(calculated_doses, roi_type):
    if roi_type == "target":
        return min(calculated_doses)
    if roi_type == "organ_at_risk":
        return max(calculated_doses)

def is_evaluated_for_repiratory_motion(clinical_goal_config):
    return clinical_goal_config['Recomp_all_phases']


###############################################################################
###############################################################################
# Run robustness evaluation range error (RE) and setup error (SE)
###############################################################################
###############################################################################

plan = case.TreatmentPlans[plan_name]
beam_set = plan.BeamSets[0]

rss_group_name = "ROB_EVAL_SE_RE"

try:
    beam_set.CreateRadiationSetScenarioGroup(Name=rss_group_name,
                                             UseIsotropicPositionUncertainty=isotropic_pos_uncertainty,
                                             PositionUncertaintySuperior=setup_error,
                                             PositionUncertaintyInferior=setup_error,
                                             PositionUncertaintyPosterior=setup_error,
                                             PositionUncertaintyAnterior=setup_error,
                                             PositionUncertaintyLeft=setup_error,
                                             PositionUncertaintyRight=setup_error,
                                             PositionUncertaintyFormation="AxesAndDiagonalEndPoints",
                                             PositionUncertaintyList=None,
                                             DensityUncertainty=range_error,
                                             NumberOfDensityDiscretizationPoints=nb_density_discretization_points,
                                             ComputeScenarioDosesAfterGroupCreation=True)
except Exception:
    print("Scenario Group" + rss_group_name + " exists already")

# Reading a dose
nominal_dose = plan.PlanOptimizations[0].TreatmentCourseSource.TotalDose
patient_model = case.PatientModel.StructureSets[ct_ref_name]
eval_setup = plan.TreatmentCourse.EvaluationSetup

## Storing Results
results = {}

print("Reading RSS Groups")
rssGroups = case.TreatmentDelivery.RadiationSetScenarioGroups
# correct group rss.Name == rss_group_name && rss.ReferencedRaditionSet.DicomPlanLabel == plan_name
rssGroup = (filter(lambda rss: rss.Name == rss_group_name and rss.ReferencedRadiationSet.DicomPlanLabel == plan_name,
                   rssGroups))[0]

if rssGroup is not None:
    print("Found corresponding RSS group " + rssGroup.Name)

discrete_doses = list(rssGroup.DiscreteFractionDoseScenarios) 


beam_set.ComputeDoseOnAdditionalSets(OnlyOneDosePerImageSet=False, AllowGridExpansion=True, ExaminationNames=[ct_ref_name], FractionNumbers=[0], ComputeBeamDoses=True)

for doe in patient.Cases[0].TreatmentDelivery.FractionEvaluations[0].DoseOnExaminations:
    if doe.OnExamination.Name == ct_ref_name:
        for eval_dose in doe.DoseEvaluations:
            if eval_dose.ForBeamSet.DicomPlanLabel == plan_name:
                evaluation_dose = eval_dose


print("Finished RSS Groups")

##########################################################################
# Get statistics based ROIs - AVERAGE DOSES 
###########################################################################

print("Reading Dose Statistics ROIs")
dose_statistics_rois = [
    {
        'label': 'CTV_45',
        'metric': 'Dmean',
        'name': 'MT_CTVt_4500',
        'doseType': 'Average',
        'roi_type': 'target',
        'priority': 1,
        'SE_RE_rob_eval': False,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'iCTV_45',
        'metric': 'Dmean',
        'name': 'MT_iCTVt_4500',
        'doseType': 'Average',
        'roi_type': 'target',
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
        
    },
    {
        'label': 'Lungs',
        'metric': 'Dmean',
        'name': 'MT_Lungs',
        'doseType': 'Average',
        'roi_type': 'target',
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
        
    },
    {
        'label': 'Heart',
        'metric': 'Dmean',
        'name': 'MT_Heart',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_L',
        'metric': 'Dmean',
        'name': 'MT_Kidney_L',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_R',
        'metric': 'Dmean',
        'name': 'MT_Kidney_R',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Spleen',
        'metric': 'Dmean',
        'name': 'MT_Spleen',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    }
]

for dose_stat_roi in dose_statistics_rois:
    try:
        
        nominal_dose_statistic = get_dose_statistic(nominal_dose, dose_stat_roi['name'],
                                                                      dose_stat_roi['doseType'])
        
        discrete_doses_statistics = map(lambda dose: get_dose_statistic(dose,dose_stat_roi['name'],
                                                                                dose_stat_roi['doseType'])*n_fractions, discrete_doses)
        

        results[get_key(dose_stat_roi)] = []
        results[get_key(dose_stat_roi)].append(round(nominal_dose_statistic,2))
        results[get_key(dose_stat_roi)].append(round(worst_dose(discrete_doses_statistics + [nominal_dose_statistic],
                                                            dose_stat_roi['roi_type']),2))
    
    except: 
        print(dose_stat_roi['name'] + " does not exist\n")
        
print("Finished Dose Statistics ROIs")

##########################################################################
# Get dose at relative volume based ROI statistics
###########################################################################

print("Reading Dose at Relative Volume ROIs")
dose_relative_volume_rois = [
    {
        'label': 'Spinal_Cord',
        'metric': 'D0_05',
        'name': 'MT_SpinalCanal',
        'relativeVolume': get_relative_volume_roi_geometries(eval_setup, evaluation_dose, 'MT_SpinalCanal', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : True,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Spinal_Cord_PRV',
        'metric': 'D0_05',
        'name': 'MT_SpinalCan_03',
        'relativeVolume': get_relative_volume_roi_geometries(eval_setup, evaluation_dose, 'MT_SpinalCanal', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Body',
        'metric': 'D0_05',
        'name': 'BODY',
        'relativeVolume': get_relative_volume_roi_geometries(eval_setup, evaluation_dose, 'BODY', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : True,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Body',
        'metric': 'D1',
        'name': 'BODY',
        'relativeVolume': get_relative_volume_roi_geometries(eval_setup, evaluation_dose, 'BODY', 1.0),
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : True,
        'Accumulate_all_phases' : False,
    }
]

for dose_relative_volume_roi in dose_relative_volume_rois:
    try: 
        
        nominal_dose_at_relative_volume_stat = get_dose_at_relative_volume(nominal_dose,
                                                                       dose_relative_volume_roi['name'],
                                                                       dose_relative_volume_roi['relativeVolume'])
        
        discrete_dose_at_relative_volume_stat = map(lambda dose: get_dose_at_relative_volume(dose,dose_relative_volume_roi['name'],
                                                                           dose_relative_volume_roi['relativeVolume'])*n_fractions, discrete_doses)
        
        results[get_key(dose_relative_volume_roi)] = []
        results[get_key(dose_relative_volume_roi)].append(round(float(nominal_dose_at_relative_volume_stat),2))
        results[get_key(dose_relative_volume_roi)].append(round(float(worst_dose(discrete_dose_at_relative_volume_stat + [nominal_dose_at_relative_volume_stat],
                                                                       dose_relative_volume_roi['roi_type'])),2))
    except:
        print(dose_relative_volume_roi['name'] + " does not exist\n")
        
print("Finished Dose at Relative Volume ROI statistics")

##########################################################################
# Get relative volume at dose level based ROI statistics
###########################################################################

print("Reading Relative Volume at Dose Value ROI statistics")
relative_volume_at_dose_level_rois = [
    {
        'label': 'iCTV_45',
        'metric': 'V95',
        'name': 'MT_iCTVt_4500',
        'dose_level': 0.95*Dprescription,
        'roi_type': "target",
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'CTV_45',
        'metric': 'V95',
        'name': 'MT_CTVt_4500',
        'dose_level': 0.95*Dprescription,
        'roi_type': "target",
        'priority': 1,
        'SE_RE_rob_eval': False,
        'Recomp_all_phases' : True,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Lung',
        'metric': 'V20',
        'name': 'MT_Lungs',
        'dose_level': 20,
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Lung',
        'metric': 'V5',
        'name': 'MT_Lungs',
        'dose_level': 5,
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Liver',
        'metric': 'V30',
        'name': 'MT_Liver',
        'dose_level': 30,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Heart',
        'metric': 'V40',
        'name': 'MT_Heart',
        'dose_level': 40,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Heart',
        'metric': 'V25',
        'name': 'MT_Heart',
        'dose_level': 25,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_L',
        'metric': 'V20',
        'name': 'MT_Kidney_L',
        'dose_level': 20,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_L',
        'metric': 'V6',
        'name': 'MT_Kidney_L',
        'dose_level': 6,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_R',
        'metric': 'V20',
        'name': 'MT_Kidney_R',
        'dose_level': 20,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Kidney_R',
        'metric': 'V6',
        'name': 'MT_Kidney_R',
        'dose_level': 6,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Bowel_cavity',
        'metric': 'V30',
        'name': 'MT_Bowel_cavity',
        'dose_level': 30,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    },
    {
        'label': 'Bowel_cavity',
        'metric': 'V45',
        'name': 'MT_Bowel_cavity',
        'dose_level': 45,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': True,
        'Recomp_all_phases' : False,
        'Accumulate_all_phases' : False,
    }
]

for relative_volume_at_dose_level_roi in relative_volume_at_dose_level_rois:
    try: 
        
        nominal_relative_volume_at_dose_stat = get_relative_volume_at_dose_value(nominal_dose,
                                                                                          relative_volume_at_dose_level_roi[
                                                                                              'name'],
                                                                                          relative_volume_at_dose_level_roi[
                                                                                              'dose_level'])
        
        descrete_relative_volume_at_dose_stats = map(lambda dose: get_relative_volume_at_dose_value(dose,relative_volume_at_dose_level_roi['name'],
                                                                                                    relative_volume_at_dose_level_roi['dose_level'])*n_fractions,discrete_doses)
        results[get_key(relative_volume_at_dose_level_roi)] = []
        results[get_key(relative_volume_at_dose_level_roi)].append(round(float(nominal_relative_volume_at_dose_stat),2))
        results[get_key(relative_volume_at_dose_level_roi)].append(round(float(worst_dose(descrete_relative_volume_at_dose_stats+[nominal_relative_volume_at_dose_stat],
                                                                       relative_volume_at_dose_level_roi['roi_type']))),2)
        
    except:
        print(relative_volume_at_dose_level_roi['name']+ " does not exist \n")
    
print("Finished Relative Volume at Dose Value ROI statistics")


print("Writing results...")

output_path = "Z:\\output_rob_eval_esophagus\\"


with open(output_path + 'clinical_goals_SE_RE_evaluation.txt', 'w+') as f:
    #writer = csv.writer(f, dialect = 'excel', delimiter = ',')
    writer = csv.writer(f, delimiter = '\t')
    writer.writerow(['ROI_ClinicalGoal', 'Nominal_scenario', 'Worst-case_scenario'])
    for key in results:
        try: 
            writer.writerow([key, results[key][0], results[key][1]])
        except:
            print("I don't know how to print "+ str(key) + " val "+ str(results[key]))

print("Written results!")
print("Done")

###############################################################################
###############################################################################
# Run robustness evaluation agains respiratory motion
###############################################################################
###############################################################################

#read phases
phases = []
for it_phase in case.ExaminationGroups[phases_group_name].Items:
    phases.append(it_phase.Examination.Name)
    
print(phases)
    
#Recompute nominal dose in all resporatory phases 
"""
beam_set.ComputeDoseOnAdditionalSets(OnlyOneDosePerImageSet=False, 
                                     AllowGridExpansion=True, 
                                     ExaminationNames= phases, 
                                     FractionNumbers=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
                                     ComputeBeamDoses=True)

"""
#find perturbed doses
evaluated_doses_respiratory_motion = []
dicom_plan_label = beam_set.DicomPlanLabel


for phase_name in phases: 
    for i,find_doe in enumerate(case.TreatmentDelivery.FractionEvaluations[0].DoseOnExaminations):
        if phase_name == find_doe.OnExamination.Name:
            print("I found the examination " + phase_name + " at DoseOnExaminations[" + str(i) + "]")
            doe = find_doe
            for eval_dose in doe.DoseEvaluations:
                if eval_dose.ForBeamSet.DicomPlanLabel == dicom_plan_label and eval_dose.PerturbedDoseProperties == None:
                    my_eval_dose = eval_dose
                    print("I found the evaluation you were looking for in " + phase_name)
    try: 
        evaluated_doses_respiratory_motion.append(my_eval_dose)
        
    except:
        print("No evaluation was found for " + phase_name)


print(evaluated_doses_respiratory_motion)


def get_all_phase_statistics(dose_phase):
    phase_statistics = {}
    
    for dose_stat_roi in filter(is_evaluated_for_repiratory_motion, dose_statistics_rois):
        try:
            phase_statistics[get_key(dose_stat_roi)] = get_dose_statistic(dose_phase, dose_stat_roi['name'],
                                                                          dose_stat_roi['doseType'])*n_fractions    
        except: 
            print(dose_stat_roi['name'] + " does not exist\n")
            
    for dose_relative_volume_roi in filter(is_evaluated_for_repiratory_motion, dose_relative_volume_rois):
        try:
            phase_statistics[get_key(dose_relative_volume_roi)] = get_dose_at_relative_volume(dose_phase, dose_relative_volume_roi['name'],
                                                                           dose_relative_volume_roi['relativeVolume'])*n_fractions    
        except: 
            print(dose_relative_volume_roi['name'] + " does not exist\n")
            
    for relative_volume_at_dose_level_roi in filter(is_evaluated_for_repiratory_motion, relative_volume_at_dose_level_rois):
        try:
            phase_statistics[get_key(relative_volume_at_dose_level_roi)] = get_relative_volume_at_dose_value(dose_phase, relative_volume_at_dose_level_roi['name'],
                                                                          relative_volume_at_dose_level_roi['dose_level'])*n_fractions    
        except: 
            print(relative_volume_at_dose_level_roi['name'] + " does not exist\n")
            
    return phase_statistics

statistics_respiratory_motion = map(get_all_phase_statistics, evaluated_doses_respiratory_motion)

with open(output_path + 'clinical_goals_repiratory_motion_evaluation.txt', 'w+') as f:
    fieldnames = ['phase_name'] + statistics_respiratory_motion[0].keys()

    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter = '\t')
    writer.writeheader()
    
    for idx,stat in enumerate(statistics_respiratory_motion):
        try: 
            stat['phase_name'] = phases[idx]
            writer.writerow(stat)
        except:
            print("I don't know how to print "+ key + " val "+ results[key])

print("Written results!")
print("Done")


