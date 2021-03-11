# Run Robustness Eval
from connect import *
import json

# find out how to stub get_current so that this auto corrects cause :(
patient = get_current("Patient")
case = get_current("Case")

# clean up into objects

plan_name = ""
ct_ref_name = "Avg CT"
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


try:
###############################################################################
###############################################################################

    plan = case.TreatmentPlans[plan_name]
    beam_set = plan.BeamSets[0]

    rss_group_name = "Rob_eval_RE_SE"

    # Run robustness evaluation range error (RE) and setup error (SE)

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

    # Reading a dose
    nominal_dose = plan.PlanOptimizations[0].TreatmentCourseSource.TotalDose
    patient_model = case.PatientModel.StructureSets[0]

    ## Storing Results
    results = {}

    # Get statistics based ROIs
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

    rssGroups = case.TreatmentDelivery.RadiationSetScenariosGroups

    # correct group rss.Name == rss_group_name && rss.ReferencedRaditionSet.DicomPlanLabel == plan_name
    rssGroup = (filter(lambda rss: rss.Name == rss_group_name and rss.ReferencedRaditionSet.DicomPlanLabel == plan_name,
                       rssGroups))[0]

    if rssGroup is not None:
        print("Found corresponding RSS group " + rssGroup.Name)

    discrete_doses = rssGroup.DiscreteFractionDoseScenarios + [nominal_dose]

    for dose_stat_roi in dose_statistics_rois:
        results[get_key(dose_stat_roi) + '_nominal'] = get_dose_statistic(nominal_dose, dose_stat_roi['name'],
                                                                          dose_stat_roi['doseType'])
        results[get_key(dose_stat_roi) + '_worst'] = worst_dose(discrete_doses,
                                                                dose_stat_roi['roi_type'],
                                                                lambda dose: get_dose_statistic(dose,
                                                                                                    dose_stat_roi['name'],
                                                                                                    dose_stat_roi['doseType']))

    # Get relative volume based ROIs
    dose_relative_volume_rois = [
        {
            'label': 'iCTV_45',
            'metric': 'V95',
            'name': 'MT_iCTVt_4500',
            'RelativeVolumes': [0.95],
            'roi_type': "target",
        },
        {
            'label': 'Spinal_Cord',
            'metric': 'D0_05',
            'name': 'MT_SpinalCanal',
            'relativeVolumes': [get_relative_volume_roi_geometries(patient_model, 'SpinalCord', 0.05)],
            'roi_type': "organ_at_risk",
        },
    ]

    for dose_relative_volume_roi in dose_relative_volume_rois:
        results[get_key(dose_relative_volume_roi) + '_nominal'] = get_dose_at_relative_volume(nominal_dose, dose_relative_volume_roi['name'], dose_relative_volume_roi['relativeVolumes'])
        results[get_key(dose_relative_volume_roi) + '_worst'] = worst_dose(discrete_doses,
                                                                           dose_relative_volume_roi['roi_type'],
                                                                           lambda dose: get_dose_at_relative_volume(dose,
                                                                                                                        dose_relative_volume_roi['name'],
                                                                                                                        dose_relative_volume_roi['relativeVolumes']))


    output_path = "Z:\\"
    with open('data.json', 'w') as f:
        json.dump(results, f)

except Exception:
    print "You broke shit."
    print str(Exception)
