"""Shared fixtures for all tests."""
import pytest
from ..models.patient_data import (
    PatientDataObject,
    ExtractionMetadata,
    Patient,
    Consultation,
    Video1Disease,
    Diagnosis,
    WhatIsHappeningInBody,
    KeyConcept,
    WhyThisPatient,
    TestResult,
    Severity,
    Video2Treatment,
    Medication,
    Warning,
    WarningSign,
    FollowUp,
    SafetyFlags,
)
from ..models.scene import SceneDefinition, SceneType


@pytest.fixture
def sample_pdo() -> PatientDataObject:
    """A minimal but valid approved PatientDataObject for testing."""
    return PatientDataObject(
        schema_version="1.0",
        extraction_metadata=ExtractionMetadata(
            document_language="fr",
            extracted_at="2024-03-15T10:00:00Z",
            extraction_confidence="high",
            requires_doctor_review=False,
            ambiguous_fields=[],
        ),
        patient=Patient(
            first_name="Jean-Paul",
            age=65,
            sex="male",
            known_conditions=["hypertension", "diabète de type 2"],
        ),
        consultation=Consultation(
            date="2024-03-15",
            doctor_name="Dr. Sophie Mercier",
            specialty="Neurologie",
            facility="Hôpital Lariboisière",
        ),
        video_1_disease=Video1Disease(
            diagnosis=Diagnosis(
                clinical_term="Maladie d'Alzheimer à un stade léger à modéré",
                plain_language="Maladie d'Alzheimer débutante",
                patient_explanation=(
                    "Votre médecin a détecté des signes précoces de la maladie d'Alzheimer. "
                    "C'est une maladie qui affecte progressivement la mémoire et la concentration."
                ),
            ),
            what_is_happening_in_the_body=WhatIsHappeningInBody(
                plain_language=(
                    "Dans votre cerveau, des protéines anormales s'accumulent et empêchent "
                    "les cellules nerveuses de communiquer correctement."
                ),
                key_concepts=[
                    KeyConcept(
                        term="Atrophie hippocampique",
                        plain_language="La zone de votre cerveau qui gère la mémoire rétrécit légèrement.",
                        visual_cue="MRI brain scan with hippocampus highlighted in blue, medical diagram",
                    )
                ],
            ),
            why_this_patient=WhyThisPatient(
                identified_risk_factors=["âge (65 ans)", "hypertension artérielle", "diabète de type 2"],
                patient_explanation=(
                    "Votre âge et vos antécédents d'hypertension et de diabète augmentent "
                    "légèrement le risque de développer cette maladie."
                ),
            ),
            test_results=[
                TestResult(
                    test_name="IRM cérébrale",
                    plain_name="Scanner du cerveau",
                    result_raw="Atrophie hippocampique bilatérale prédominante",
                    result_plain="Le scanner montre que la zone mémoire de votre cerveau est légèrement réduite.",
                    visual_cue="MRI brain scan showing bilateral hippocampal atrophy, clinical image",
                ),
                TestResult(
                    test_name="MMSE",
                    plain_name="Test de mémoire",
                    result_raw="Score de 22/30",
                    result_plain="Votre score au test de mémoire indique un déficit léger à modéré.",
                    visual_cue=None,
                ),
            ],
            severity=Severity(
                level="moderate",
                plain_language=(
                    "Votre situation est au stade léger à modéré. "
                    "Avec le bon traitement, il est possible de ralentir l'évolution."
                ),
            ),
            scene_plan=[
                SceneDefinition(scene=1, type=SceneType.avatar, duration_sec=18, content="video_1_disease.diagnosis.patient_explanation"),
                SceneDefinition(scene=2, type=SceneType.visual, duration_sec=20, content="video_1_disease.what_is_happening_in_the_body.key_concepts.0", visual_cue="MRI brain scan with hippocampus highlighted in blue"),
                SceneDefinition(scene=3, type=SceneType.avatar, duration_sec=18, content="video_1_disease.why_this_patient.patient_explanation"),
                SceneDefinition(scene=4, type=SceneType.visual, duration_sec=20, content="video_1_disease.test_results.0.result_plain", visual_cue="MRI brain scan showing bilateral hippocampal atrophy"),
                SceneDefinition(scene=5, type=SceneType.avatar, duration_sec=18, content="video_1_disease.severity.plain_language"),
            ],
        ),
        video_2_treatment=Video2Treatment(
            medications=[
                Medication(
                    name="Donépézil",
                    brand_name="Aricept",
                    plain_language="Ce médicament aide les cellules du cerveau à mieux communiquer entre elles.",
                    dosage="5 mg",
                    frequency="1 fois par jour",
                    timing="le soir au coucher",
                    form="tablet",
                    with_food=False,
                    duration="indéfinie",
                    visual_cue="white round pill next to a glass of water, clean medical photography",
                ),
                Medication(
                    name="Mémantine",
                    brand_name="Ebixa",
                    plain_language="Ce médicament protège les cellules nerveuses et aide à maintenir vos capacités cognitives.",
                    dosage="10 mg",
                    frequency="2 fois par jour",
                    timing="matin et soir",
                    form="tablet",
                    with_food=True,
                    duration="indéfinie",
                    visual_cue="two white tablets on a table with a meal in background, medical photography",
                ),
            ],
            important_warnings=[
                Warning(warning="Ne pas arrêter le Donépézil sans consulter votre médecin.", severity="high"),
                Warning(warning="Des nausées peuvent apparaître au début du traitement — elles disparaissent généralement après quelques jours.", severity="medium"),
            ],
            precautions_daily_life=[
                "Marchez 30 minutes par jour pour aider votre cerveau et votre cœur.",
                "Faites des activités qui font travailler votre mémoire : lecture, mots croisés.",
                "Suivez votre régime alimentaire adapté au diabète.",
                "Évitez de boire de l'alcool.",
            ],
            warning_signs_to_watch=[
                WarningSign(
                    sign="Chute ou confusion soudaine",
                    action="Appelez immédiatement votre médecin ou le 15.",
                    urgency="urgent",
                ),
                WarningSign(
                    sign="Nausées ou diarrhées persistantes après plus d'une semaine",
                    action="Contactez votre médecin pour ajuster le traitement.",
                    urgency="medium",
                ),
            ],
            follow_up=FollowUp(
                next_appointment="dans 3 mois (juin 2024)",
                specialist="Dr. Sophie Mercier, Neurologue",
                what_to_bring="Votre carnet de santé et la liste de vos médicaments actuels.",
                additional_referrals=["Dr. Ahmed Benali, Gériatre — Centre mémoire Lariboisière"],
            ),
            scene_plan=[
                SceneDefinition(scene=1, type=SceneType.avatar, duration_sec=14, content="video_2_treatment.medications introduction"),
                SceneDefinition(scene=2, type=SceneType.visual, duration_sec=16, content="video_2_treatment.medications.0", visual_cue="white round pill next to a glass of water, clean medical photography"),
                SceneDefinition(scene=3, type=SceneType.visual, duration_sec=16, content="video_2_treatment.medications.1", visual_cue="two white tablets on a table with a meal in background"),
                SceneDefinition(scene=4, type=SceneType.avatar, duration_sec=14, content="video_2_treatment.important_warnings"),
                SceneDefinition(scene=5, type=SceneType.visual, duration_sec=16, content="video_2_treatment.precautions_daily_life", visual_cue="elderly person on a morning walk, outdoor, soft light"),
                SceneDefinition(scene=6, type=SceneType.visual, duration_sec=16, content="video_2_treatment.warning_signs_to_watch", visual_cue="red warning icon with list of symptoms, medical infographic style"),
                SceneDefinition(scene=7, type=SceneType.avatar, duration_sec=14, content="video_2_treatment.follow_up"),
            ],
        ),
        safety_flags=SafetyFlags(
            drug_interactions_detected=False,
            allergy_conflict=False,
            missing_critical_info=[],
            requires_pharmacist_review=False,
        ),
        doctor_approved=True,
        approved_at="2024-03-15T10:05:00Z",
    )
