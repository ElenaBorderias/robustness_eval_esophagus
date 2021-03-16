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

# other (thanks :( as in white walkers??????) parameters
isotropic_pos_uncertainty = False
nb_density_discretization_points = 2


###############################################################################

######### FUNCTIONS #########

def get_relative_volume_roi_geometries(patient_model, name, goal_volume=0.05):
    abs_vol = patient_model.RoiGeometries[name].GetRoiVolume()
    relative_volume = float((goal_volume * 100) / abs_vol)
    return relative_volume


def get_key(value):
    return value['label'] + '_' + value['metric']


def get_dose_statistic(dose, roi_name, dose_type):
    return round(dose.GetDoseStatistic(RoiName=roi_name, DoseType=dose_type) * 0.01, 2)


def get_dose_at_relative_volume(dose, roi_name, relative_volume):
    return round(float(
        dose.GetDoseAtRelativeVolumes(RoiName=roi_name,
                                      RelativeVolumes=[relative_volume])[0]) * 0.01, 2)

def get_relative_volume_at_dose_value(dose, roi_name, dose_value):
    return round(float(
        dose.GetDoseAtRelativeVolumes(RoiName=roi_name,
                                      DoseValues=[dose_value])[0]), 2)
        


def worst_dose(doses, roi_type, dose_calculation):
    calculated_doses = map(dose_calculation, doses)
    if roi_type == "target":
        return min(calculated_doses)
    if roi_type == "organ_at_risk":
        return max(calculated_doses)


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

## Storing Results
results = {}

print("Reading RSS Groups")
rssGroups = case.TreatmentDelivery.RadiationSetScenarioGroups
# correct group rss.Name == rss_group_name && rss.ReferencedRaditionSet.DicomPlanLabel == plan_name
rssGroup = (filter(lambda rss: rss.Name == rss_group_name and rss.ReferencedRadiationSet.DicomPlanLabel == plan_name,
                   rssGroups))[0]

if rssGroup is not None:
    print("Found corresponding RSS group " + rssGroup.Name)

discrete_doses = list(rssGroup.DiscreteFractionDoseScenarios) + [nominal_dose]

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
        'SE_RE_rob_eval': 'False',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'iCTV_45',
        'metric': 'Dmean',
        'name': 'MT_iCTVt_4500',
        'doseType': 'Average',
        'roi_type': 'target',
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
        
    },
    {
        'label': 'Lungs',
        'metric': 'Dmean',
        'name': 'MT_Lungs',
        'doseType': 'Average',
        'roi_type': 'target',
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
        
    },
    {
        'label': 'Heart',
        'metric': 'Dmean',
        'name': 'MT_Heart',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Kidneys',
        'metric': 'Dmean',
        'name': 'MT_Kidneys',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Spleen',
        'metric': 'Dmean',
        'name': 'MT_Spleen',
        'doseType': 'Average',
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    }
]

for dose_stat_roi in dose_statistics_rois:
    try:
        
        results[get_key(dose_stat_roi)] = []
        results[get_key(dose_stat_roi)].append(get_dose_statistic(nominal_dose, dose_stat_roi['name'],
                                                                      dose_stat_roi['doseType']))
        results[get_key(dose_stat_roi)].append(worst_dose(discrete_doses,
                                                            dose_stat_roi['roi_type'],
                                                            lambda dose: get_dose_statistic(dose,
                                                                                            dose_stat_roi['name'],
                                                                                            dose_stat_roi[
                                                                                                'doseType'])))
    except: 
        del results[get_key(dose_stat_roi)]
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
        'relativeVolume': get_relative_volume_roi_geometries(patient_model, 'MT_SpinalCanal', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Spinal_Cord_PRV',
        'metric': 'D0_05',
        'name': 'MT_SpinalCan_03',
        'relativeVolume': get_relative_volume_roi_geometries(patient_model, 'MT_SpinalCanal', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Body',
        'metric': 'D0_05',
        'name': 'BODY',
        'relativeVolume': get_relative_volume_roi_geometries(patient_model, 'BODY', 0.05),
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Body',
        'metric': 'D1',
        'name': 'BODY',
        'relativeVolume': get_relative_volume_roi_geometries(patient_model, 'BODY', 1.0),
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    }
]

for dose_relative_volume_roi in dose_relative_volume_rois:
    try: 
        results[get_key(dose_relative_volume_roi)] = []
        results[get_key(dose_relative_volume_roi)].append(get_dose_at_relative_volume(nominal_dose,
                                                                                          dose_relative_volume_roi[
                                                                                              'name'],
                                                                                          dose_relative_volume_roi[
                                                                                              'relativeVolume']))
        results[get_key(dose_relative_volume_roi)].append(worst_dose(discrete_doses,
                                                                       dose_relative_volume_roi['roi_type'],
                                                                       lambda dose: get_dose_at_relative_volume(
                                                                           dose,
                                                                           dose_relative_volume_roi['name'],
                                                                           dose_relative_volume_roi[
                                                                               'relativeVolume'])))
    except:
        del results[get_key(dose_relative_volume_roi)]
        print(dose_stat_roi['name'] + " does not exist\n")
        
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
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Lung',
        'metric': 'V20',
        'name': 'MT_Lungs',
        'dose_level': 20,
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Lung',
        'metric': 'V5',
        'name': 'MT_Lungs',
        'dose_level': 5,
        'roi_type': "organ_at_risk",
        'priority': 1,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Liver',
        'metric': 'V30',
        'name': 'MT_Liver',
        'dose_level': 30,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Heart',
        'metric': 'V40',
        'name': 'MT_Liver',
        'dose_level': 40,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Heart',
        'metric': 'V25',
        'name': 'MT_Liver',
        'dose_level': 25,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Kidneys',
        'metric': 'V20',
        'name': 'MT_Kidneys',
        'dose_level': 20,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Kidneys',
        'metric': 'V6',
        'name': 'MT_Kidneys',
        'dose_level': 6,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Bowel_cavity',
        'metric': 'V30',
        'name': 'MT_Bowel_cavity',
        'dose_level': 30,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    },
    {
        'label': 'Bowel_cavity',
        'metric': 'V45',
        'name': 'MT_Bowel_cavity',
        'dose_level': 45,
        'roi_type': "organ_at_risk",
        'priority': 2,
        'SE_RE_rob_eval': 'True',
        'Recomp_all_phases' : 'False',
        'Accumulate_all_phases' : 'False',
    }
]

for relative_volume_at_dose_level_roi in relative_volume_at_dose_level_rois:
    try: 
        results[get_key(relative_volume_at_dose_level_roi)] = []
        results[get_key(relative_volume_at_dose_level_roi)].append(get_relative_volume_at_dose_value(nominal_dose,
                                                                                          relative_volume_at_dose_level_roi[
                                                                                              'name'],
                                                                                          relative_volume_at_dose_level_roi[
                                                                                              'dose_level']))
        results[get_key(relative_volume_at_dose_level_roi)].append(worst_dose(discrete_doses,
                                                                       relative_volume_at_dose_level_roi['roi_type'],
                                                                       lambda dose: get_relative_volume_at_dose_value(
                                                                           dose,
                                                                           relative_volume_at_dose_level_roi['name'],
                                                                           relative_volume_at_dose_level_roi[
                                                                               'dose_level'])))
    except:
        del results[get_key(relative_volume_at_dose_level_roi)]
        print(dose_stat_roi['name'] + " does not exist \n")
    
print("Finished Relative Volume at Dose Value ROI statistics")


print("Writing results...")

output_path = "Z:\\output_path_rob_eval_esophagus"


with open(output_path + 'data.csv', 'wb') as f:
    writer = csv.writer(f, delimiter = ',')
    writer.writerow(['roi', 'nominal', 'worst_case'])
    for key in results:
        writer.writerow([key, results[key][0], results[key][1]])

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
    
#Recompute nominal dose in all resporatory phases 
beam_set.ComputeDoseOnAdditionalSets(OnlyOneDosePerImageSet=False, 
                                     AllowGridExpansion=True, 
                                     ExaminationNames= phases, 
                                     FractionNumbers=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
                                     ComputeBeamDoses=True)
#find perturbed doses
evaluated_doses_respiratory_motion = []

for i,phase_name in enumerate(phases): 
    if phase_name == case.TreatmentDelivery.FractionEvaluations[0].DoseOnExaminations[i].OnExamination.Name:
        print("I found the examination")
        doe = case.TreatmentDelivery.FractionEvaluations[0].DoseOnExaminations[i]
        for eval_dose in doe.DoseEvaluations:
            if eval_dose.ForBeamSet.DicomPlanLabel == dicom_plan_label and eval_dose.PerturbedDoseProperties == None:
                evaluated_doses_respiratory_motion.append(eval_dose)



