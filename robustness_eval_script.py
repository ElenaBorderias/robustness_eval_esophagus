# Run Robustness Eval
from connect import *

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


# def worse_dose_roi(doses, roi):
#


###############################################################################
###############################################################################

plan = case.TreatmentPlans[plan_name]
beam_set = plan.BeamSets[0]

# Run robustness evaluation range error (RE) and setup error (SE)

beam_set.CreateRadiationSetScenarioGroup(Name=r"Rob_eval_RE_SE",
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
    },
    {
        'label': 'iCTV_45',
        'metric': 'Dmean',
        'name': 'MT_iCTVt_4500',
        'doseType': 'Average',
    }
]

for dose_stat_roi in dose_statistics_rois:
    results[get_key(dose_stat_roi)] = round(
        nominal_dose.GetDoseStatistic(RoiName=dose_stat_roi['name'], DoseType=dose_stat_roi['doseType']) * 0.01, 2)

dose_relative_volume_rois = [
    {
        'label': 'iCTV_45',
        'metric': 'V95',
        'name': 'MT_CTVt_4500',
        'RelativeVolumes': [0.95],
    },
    {
        'label': 'Spinal_Cord',
        'metric': 'D0_05',
        'name': 'SpinalCord',
        'relativeVolumes': [get_relative_volume_roi_geometries(patient_model, 'SpinalCord', 0.05)],
    },
]

for dose_relative_volume_roi in dose_relative_volume_rois:
    results[get_key(dose_relative_volume_roi)] = round(float(
        nominal_dose.GetDoseAtRelativeVolumes(RoiName=dose_relative_volume_roi['name'],
                                              RelativeVolumes=dose_relative_volume_roi['relativeVolumes'])) * 0.01, 2)

