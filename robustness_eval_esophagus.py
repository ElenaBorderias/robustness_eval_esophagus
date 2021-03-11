# Run Robustness Eval
from connect import *
import json

# find out how to stub get_current so that this auto corrects cause :(
patient = get_current("Patient")
case = get_current("Case")

# clean up into objects

plan_name = "Average_7mm_DO_s"
ct_ref_name = "Average CT"
phases_group_name = "Phases"
setup_error = 0.7  # mm
range_error = 3  # %

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


def get_dose_at_relative_volume(dose, roi_name, relative_volumes):
    return round(float(
        dose.GetDoseAtRelativeVolumes(RoiName=roi_name,
                                      RelativeVolumes=relative_volumes)) * 0.01, 2)


def worst_dose(doses, roi_type, dose_calculation):
    calculated_doses = map(dose_calculation, doses)
    if roi_type == "target":
        return min(calculated_doses)
    if roi_type == "organ_at_risk":
        return max(calculated_doses)



###############################################################################
###############################################################################

plan = case.TreatmentPlans[plan_name]
beam_set = plan.BeamSets[0]

rss_group_name = "ROB_EVAL_SE_RE"

# Run robustness evaluation range error (RE) and setup error (SE)
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

# Get statistics based ROIs
print("Reading Dose Statistics ROIs")
dose_statistics_rois = [
    {
        'label': 'CTV_45',
        'metric': 'Dmean',
        'name': 'MT_CTVt_4500',
        'doseType': 'Average',
        'roi_type': 'target',
    },
    {
        'label': 'iCTV_45',
        'metric': 'Dmean',
        'name': 'MT_iCTVt_4500',
        'doseType': 'Average',
        'roi_type': 'target',
    }
]

for dose_stat_roi in dose_statistics_rois:
    results[get_key(dose_stat_roi) + '_nominal'] = get_dose_statistic(nominal_dose, dose_stat_roi['name'],
                                                                      dose_stat_roi['doseType'])
    results[get_key(dose_stat_roi) + '_worst'] = worst_dose(discrete_doses,
                                                            dose_stat_roi['roi_type'],
                                                            lambda dose: get_dose_statistic(dose,
                                                                                            dose_stat_roi['name'],
                                                                                            dose_stat_roi[
                                                                                                'doseType']))
print("Finished Dose Statistics ROIs")


# Get relative volume based ROIs
print("Reading Dose Relative Volume ROIs")
dose_relative_volume_rois = [
    {
        'label': 'iCTV_45',
        'metric': 'V95',
        'name': 'MT_iCTVt_4500',
        'relativeVolumes': [0.95],
        'roi_type': "target",
    },
    {
        'label': 'Spinal_Cord',
        'metric': 'D0_05',
        'name': 'MT_SpinalCanal',
        'relativeVolumes': [get_relative_volume_roi_geometries(patient_model, 'MT_SpinalCanal', 0.05)],
        'roi_type': "organ_at_risk",
    },
]

for dose_relative_volume_roi in dose_relative_volume_rois:
    results[get_key(dose_relative_volume_roi) + '_nominal'] = get_dose_at_relative_volume(nominal_dose,
                                                                                          dose_relative_volume_roi[
                                                                                              'name'],
                                                                                          dose_relative_volume_roi[
                                                                                              'relativeVolumes'])
    results[get_key(dose_relative_volume_roi) + '_worst'] = worst_dose(discrete_doses,
                                                                       dose_relative_volume_roi['roi_type'],
                                                                       lambda dose: get_dose_at_relative_volume(
                                                                           dose,
                                                                           dose_relative_volume_roi['name'],
                                                                           dose_relative_volume_roi[
                                                                               'relativeVolumes']))
print("Finished Dose Relative Volume ROIs")

print("Writing results...")
output_path = "Z:\\"
with open('data.json', 'w') as f:
    json.dump(results, f)
print("Written results!")
print("Done")
