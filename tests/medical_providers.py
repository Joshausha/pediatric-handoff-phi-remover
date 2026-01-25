"""
Custom Faker providers for medical/pediatric PHI generation.

These providers generate realistic medical identifiers and pediatric-specific
data that Presidio should detect as PHI.
"""

import random
from faker.providers import BaseProvider


class MedicalRecordProvider(BaseProvider):
    """Provider for Medical Record Numbers (MRN) in various formats."""

    def mrn(self) -> str:
        """Generate an MRN in various hospital formats."""
        formats = [
            lambda: str(self.random_int(min=10000000, max=99999999)),  # 8 digits
            lambda: str(self.random_int(min=1000000, max=9999999)),   # 7 digits
            lambda: f"MRN{self.random_int(min=1000000, max=9999999)}",
            lambda: f"MRN {self.random_int(min=10000000, max=99999999)}",
        ]
        return self.random_element(formats)()

    def mrn_numeric(self) -> str:
        """Generate a purely numeric MRN (for hash prefix)."""
        return str(self.random_int(min=10000000, max=99999999))

    def pager_number(self) -> str:
        """Generate a hospital pager number."""
        formats = [
            lambda: f"#{self.random_int(min=1000, max=9999)}",
            lambda: str(self.random_int(min=10000, max=99999)),
            lambda: f"{self.random_int(min=100, max=999)}-{self.random_int(min=1000, max=9999)}",
        ]
        return self.random_element(formats)()


class PediatricAgeProvider(BaseProvider):
    """Provider for detailed pediatric ages."""

    def pediatric_age(self) -> str:
        """Generate a pediatric age in various detailed formats."""
        age_type = self.random_element([
            "newborn", "infant_days", "infant_weeks", "infant_months",
            "toddler", "child", "adolescent"
        ])

        if age_type == "newborn":
            days = self.random_int(min=0, max=7)
            hours = self.random_int(min=0, max=23)
            if days == 0:
                return f"{hours} hours old"
            return self.random_element([
                f"{days} day old",
                f"{days} days old",
                f"DOL {days}",
                f"day of life {days}",
            ])

        elif age_type == "infant_days":
            days = self.random_int(min=1, max=28)
            return self.random_element([
                f"{days} days old",
                f"{days} day old",
            ])

        elif age_type == "infant_weeks":
            weeks = self.random_int(min=1, max=12)
            days = self.random_int(min=0, max=6)
            if days > 0:
                return f"{weeks} weeks {days} days old"
            return f"{weeks} weeks old"

        elif age_type == "infant_months":
            months = self.random_int(min=1, max=24)
            return self.random_element([
                f"{months} month old",
                f"{months} months old",
                f"{months}mo",
                f"{months} mo old",
            ])

        elif age_type == "toddler":
            years = self.random_int(min=2, max=4)
            return self.random_element([
                f"{years} year old",
                f"{years} years old",
                f"{years}yo",
                f"{years} yo",
            ])

        elif age_type == "child":
            years = self.random_int(min=5, max=12)
            return self.random_element([
                f"{years} year old",
                f"{years} years old",
                f"{years}yo",
            ])

        else:  # adolescent
            years = self.random_int(min=13, max=17)
            return self.random_element([
                f"{years} year old",
                f"{years} years old",
                f"{years}yo",
            ])

    def gestational_age(self) -> str:
        """Generate gestational age for preterm infants."""
        weeks = self.random_int(min=23, max=40)
        days = self.random_int(min=0, max=6)

        formats = [
            f"{weeks}",
            f"{weeks} {days}/7",
            f"{weeks}+{days}",
        ]
        return self.random_element(formats)


class RoomNumberProvider(BaseProvider):
    """Provider for hospital room and bed numbers."""

    def room_number(self) -> str:
        """Generate a room or bed number."""
        room_type = self.random_element([
            "standard", "picu_bed", "nicu_bed", "floor_room", "er_bay"
        ])

        if room_type == "standard":
            return str(self.random_int(min=100, max=999))

        elif room_type == "picu_bed":
            bed = self.random_int(min=1, max=24)
            return self.random_element([
                str(bed),
                f"bed {bed}",
                f"Bed {bed}",
            ])

        elif room_type == "nicu_bed":
            bed = self.random_int(min=1, max=60)
            return self.random_element([
                str(bed),
                f"bed {bed}",
                f"isolette {bed}",
            ])

        elif room_type == "floor_room":
            floor = self.random_int(min=2, max=9)
            room = self.random_int(min=1, max=40)
            return self.random_element([
                f"{floor}{room:02d}",
                f"{floor}-{room:02d}",
            ])

        else:  # er_bay
            bay = self.random_int(min=1, max=30)
            return self.random_element([
                str(bay),
                f"bay {bay}",
                f"Bay {bay}",
            ])


class ClinicalContentProvider(BaseProvider):
    """Provider for realistic clinical content (non-PHI)."""

    MEDICATIONS = [
        "albuterol", "ceftriaxone", "azithromycin", "amoxicillin", "ibuprofen",
        "acetaminophen", "ondansetron", "dexamethasone", "prednisolone", "fluticasone",
        "vancomycin", "piperacillin-tazobactam", "ampicillin", "gentamicin",
        "levetiracetam", "phenobarbital", "morphine", "fentanyl", "ketamine",
        "insulin", "epinephrine", "norepinephrine", "dopamine", "milrinone",
    ]

    CONDITIONS = [
        "bronchiolitis", "pneumonia", "asthma exacerbation", "croup", "cellulitis",
        "UTI", "gastroenteritis", "appendicitis", "diabetic ketoacidosis", "seizure",
        "febrile neutropenia", "sickle cell crisis", "respiratory failure",
        "sepsis", "meningitis", "viral syndrome", "dehydration", "failure to thrive",
        "congenital heart disease", "BPD", "hyperbilirubinemia", "NEC",
    ]

    RESPIRATORY_SUPPORT = [
        "room air", "nasal cannula", "high flow nasal cannula", "CPAP", "BiPAP",
        "mechanical ventilation", "HFOV", "2L NC", "4L NC", "HFNC 2L/kg",
    ]

    SYMPTOMS = [
        "fever", "cough", "wheezing", "increased work of breathing", "vomiting",
        "diarrhea", "abdominal pain", "lethargy", "poor feeding", "irritability",
        "rash", "seizure activity", "apnea", "desaturation", "tachycardia",
    ]

    SERVICE_NEEDS = [
        "housing assistance", "transportation", "medication assistance",
        "home health", "DME setup", "interpreter services", "food assistance",
    ]

    RELATIONSHIPS = [
        "mother", "father", "grandmother", "grandfather", "aunt", "uncle",
        "foster parent", "guardian", "stepmother", "stepfather",
    ]

    GENDERS = ["male", "female"]

    DELIVERY_TYPES = [
        "C-section", "NSVD", "vacuum-assisted delivery", "forceps delivery",
        "scheduled cesarean", "emergent cesarean",
    ]

    FREQUENCIES = ["4h", "6h", "8h", "12h", "24h", "PRN", "BID", "TID", "QID"]

    PARAMETERS = [
        "respiratory status", "temperature", "blood pressure", "urine output",
        "feeding tolerance", "pain", "neurological status", "glucose",
    ]

    HOSPITALS = [
        "Children's Hospital", "University Medical Center", "Community Hospital",
        "Regional Medical Center", "Memorial Hospital", "General Hospital",
    ]

    def medication(self) -> str:
        return self.random_element(self.MEDICATIONS)

    def condition(self) -> str:
        return self.random_element(self.CONDITIONS)

    def respiratory_support(self) -> str:
        return self.random_element(self.RESPIRATORY_SUPPORT)

    def symptom(self) -> str:
        return self.random_element(self.SYMPTOMS)

    def service_need(self) -> str:
        return self.random_element(self.SERVICE_NEEDS)

    def relationship(self) -> str:
        return self.random_element(self.RELATIONSHIPS)

    def gender(self) -> str:
        return self.random_element(self.GENDERS)

    def delivery_type(self) -> str:
        return self.random_element(self.DELIVERY_TYPES)

    def frequency(self) -> str:
        return self.random_element(self.FREQUENCIES)

    def parameter(self) -> str:
        return self.random_element(self.PARAMETERS)

    def hospital_name(self) -> str:
        return self.random_element(self.HOSPITALS)

    def school_name(self) -> str:
        """Generate a school name."""
        types = ["Elementary", "Middle School", "Academy", "Montessori"]
        names = [
            "Jefferson", "Lincoln", "Washington", "Roosevelt", "Kennedy",
            "Oak Park", "Riverside", "Hillside", "Lakewood", "Maple Grove",
        ]
        return f"{self.random_element(names)} {self.random_element(types)}"

    def clinic_name(self) -> str:
        """Generate a clinic/practice name."""
        names = [
            "Pediatric Associates", "Children's Clinic", "Family Medicine",
            "Pediatric Partners", "Kids First Pediatrics", "Community Pediatrics",
        ]
        return self.random_element(names)

    def pharmacy(self) -> str:
        """Generate a pharmacy name."""
        names = [
            "CVS Pharmacy", "Walgreens", "Rite Aid", "Walmart Pharmacy",
            "Target Pharmacy", "Costco Pharmacy", "Hospital Pharmacy",
        ]
        return self.random_element(names)

    def concern(self) -> str:
        """Generate a patient/family concern."""
        concerns = [
            "medication side effects", "discharge instructions",
            "follow-up appointment", "test results", "diet questions",
            "activity restrictions", "school note", "work excuse",
        ]
        return self.random_element(concerns)

    def fio2(self) -> str:
        return str(self.random_int(min=21, max=100))

    def saturation(self) -> str:
        return str(self.random_int(min=88, max=100))

    def target_sat(self) -> str:
        return str(self.random_int(min=90, max=95))

    def ph(self) -> str:
        return f"7.{self.random_int(min=20, max=45)}"

    def pco2(self) -> str:
        return str(self.random_int(min=25, max=70))

    def po2(self) -> str:
        return str(self.random_int(min=50, max=150))

    def anc(self) -> str:
        return str(self.random_int(min=0, max=500))

    def antibiotic(self) -> str:
        return self.random_element([
            "cefepime", "vancomycin", "meropenem", "piperacillin-tazobactam"
        ])

    def trend_direction(self) -> str:
        return self.random_element(["improving", "stable", "worsening"])

    def current_support(self) -> str:
        return self.random_element([
            "HFNC 2L/kg", "BiPAP", "increased home O2", "4L NC"
        ])

    def escalation_med(self) -> str:
        return self.random_element([
            "IV methylprednisolone", "terbutaline", "magnesium sulfate",
            "epinephrine", "racemic epinephrine"
        ])

    def hours(self) -> str:
        return str(self.random_int(min=1, max=6))

    def number(self) -> str:
        return str(self.random_int(min=1, max=14))

    def treatment(self) -> str:
        return self.random_element([
            "IV antibiotics", "steroids", "phototherapy", "TPN",
            "continuous feeds", "respiratory support"
        ])

    def weight(self) -> str:
        """Generate a weight for infants/children."""
        weight_type = self.random_element(["grams", "kg"])
        if weight_type == "grams":
            return f"{self.random_int(min=500, max=5000)}g"
        return f"{self.random_int(min=2, max=50)}.{self.random_int(min=0, max=9)} kg"


# Provider registry for easy addition to Faker
CUSTOM_PROVIDERS = [
    MedicalRecordProvider,
    PediatricAgeProvider,
    RoomNumberProvider,
    ClinicalContentProvider,
]
