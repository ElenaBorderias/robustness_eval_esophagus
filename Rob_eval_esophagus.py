# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 15:48:00 2020

@author: elena.borderias

This script runs the robustness test for Esophagus patients according to PROTECT protocol 
(1)
(2)
(3)
"""

from connect import *
patient = get_current("Patient")
case = get_current("Case")

plan_name = ""
ct_ref_name = "Avg CT"
phases_group_name = "Phases"
setup_error = 0.7 #mm
range_error = 3 #%
 
#other parameters
isotropic_pos_uncertainty = False
nb_density_discretization_points = 2


###############################################################################
###############################################################################
###############################################################################

plan = case.TreatmentPlans[plan_name]
beam_set = plan.BeamSets[0]

#Run robustness evaluation range error (RE) and setup error (SE)

beam_set.CreateRadiationSetScenarioGroup(Name=r"Rob_eval_RE_SE", 
                                         UseIsotropicPositionUncertainty= isotropic_pos_uncertainty,
                                         PositionUncertaintySuperior= setup_error, 
                                         PositionUncertaintyInferior= setup_error, 
                                         PositionUncertaintyPosterior= setup_error, 
                                         PositionUncertaintyAnterior= setup_error, 
                                         PositionUncertaintyLeft= setup_error, 
                                         PositionUncertaintyRight= setup_error, 
                                         PositionUncertaintyFormation="AxesAndDiagonalEndPoints", 
                                         PositionUncertaintyList=None, 
                                         DensityUncertainty= range_error, 
                                         NumberOfDensityDiscretizationPoints= nb_density_discretization_points,
                                         ComputeScenarioDosesAfterGroupCreation=True)

#export clinical goals corresponding to PROTECT table.3.1 for iCTV and table.3.2

#0 index correspond to nominal dose, #1 corresponds to worst-scenario 

##ictv goals
ictv_Dmean = []
ictv_V95 = []

## oar goals 
#first priority
spinal_cord_D0_05 = []
spinal_cord_prv_D0_05 = []
lungs_Dmean = []
lungs_V20 = []
lungs_V5 = []
body_D0_05 = []
body_D1 = []

abs_vol_spinalcord = case.PatientModel.StructureSets[0].RoiGeometries["SpinalCord"].GetRoiVolume()
rel_vol_0_05_spinalcord = float((0.05*100)/abs_vol_spinalcord)

abs_vol_spinal_cord_prv = case.PatientModel.StructureSets[0].RoiGeometries["SpinalCord_PRV"].GetRoiVolume()
rel_vol_0_05_spinal_cord_prv = float((0.05*100)/abs_vol_spinal_cord_prv)

abs_vol_body = case.PatientModel.StructureSets[0].RoiGeometries["Body"].GetRoiVolume()
rel_vol_0_05_body = float((0.05*100)/abs_vol_body)
rel_vol_1_body = float((1*100)/abs_vol_body)


#second priority
liver_V30 = []
heart_V40 = []
heart_V25 = []
hear_Dmean = []
kidneys_Dmean = []
kidneys_V20 = []
kidneys_V6 = []
bowel_cavity_V30 = []
bowel_cavity_V45 = []
stomach-ictv_D0_5 = []
spleen_Dmean = []

##get nominal values 

dose = case.TreatmentPlans[p].PlanOptimizations[0].TreatmentCourseSource.TotalDose

CTVp_7000_D98.append(round(float(dose.GetDoseAtRelativeVolumes(RoiName ="CTVp_7000", RelativeVolumes= [0.98]))*0.01,2))
CTVn_7000_D98.append(round(float(dose.GetDoseAtRelativeVolumes(RoiName ="CTVn_7000", RelativeVolumes= [0.98]))*0.01,2))
CTVn_5425_D98.append(round(float(dose.GetDoseAtRelativeVolumes(RoiName ="CTVn_5425", RelativeVolumes= [0.98]))*0.01,2))
parotid_R.append(round(dose.GetDoseStatistic(RoiName ="Parotid_R", DoseType="Average")*0.01,2))
parotid_L.append(round(dose.GetDoseStatistic(RoiName ="Parotid_L", DoseType="Average")*0.01,2))

    


#Run robustness evaluation towards respiratory motion 

#0 index correspond to nominal dose, #1 corresponds to worst-scenario 

##ictv goals
ictv_V95_rm = []

## oar goals 
#first priority
spinal_cord_D0_05_rm = []
spinal_cord_prv_D0_05_rm = []
lungs_Dmean_rm = []
lungs_V20_rm = []
lungs_V5_rm = []
body_D0_05_rm = []
body_D1_rm = []

#second priority
liver_V30_rm = []
heart_V40_rm = []
heart_V25_rm = []
hear_Dmea_rm = []
kidneys_Dmean_rm = []
kidneys_V20_rm = []
kidneys_V6_rm = []
bowel_cavity_V30_rm = []
bowel_cavity_V45_rm = []
stomach-ictv_D0_5_rm = []
spleen_Dmean_rm = []















