import random

from django.core.management.base import BaseCommand

from apps.pharmacy.models import Medicine, UnitType

MEDICINES = [
    ("Paracetamol", UnitType.TABLET, "Analgesic / antipyretic. Used for fever and mild to moderate pain.", 500),
    ("Ibuprofen", UnitType.TABLET, "NSAID for pain, inflammation and fever.", 400),
    ("Naproxen", UnitType.TABLET, "NSAID for moderate pain and inflammation.", 300),
    ("Diclofenac Sodium", UnitType.TABLET, "NSAID for joint and muscle pain.", 350),
    ("Aspirin", UnitType.TABLET, "Antiplatelet and analgesic.", 400),
    ("Ketorolac", UnitType.ML, "Injectable NSAID for acute severe pain.", 100),
    ("Tramadol", UnitType.CAPSULE, "Opioid analgesic for moderate to severe pain.", 200),
    ("Morphine Sulfate", UnitType.ML, "Opioid analgesic injection for severe pain.", 60),
    ("Codeine Phosphate", UnitType.TABLET, "Opioid analgesic used for cough and mild pain.", 150),
    ("Pethidine", UnitType.ML, "Opioid analgesic injection used for acute pain.", 80),
    ("Amoxicillin", UnitType.CAPSULE, "Broad-spectrum penicillin antibiotic.", 600),
    ("Amoxicillin/Clavulanate", UnitType.TABLET, "Combination penicillin antibiotic.", 500),
    ("Azithromycin", UnitType.TABLET, "Macrolide antibiotic for respiratory and skin infections.", 450),
    ("Ciprofloxacin", UnitType.TABLET, "Fluoroquinolone antibiotic for urinary and GI infections.", 400),
    ("Levofloxacin", UnitType.TABLET, "Fluoroquinolone antibiotic for respiratory and urinary infections.", 350),
    ("Metronidazole", UnitType.TABLET, "Antibiotic/antiprotozoal for anaerobic infections.", 500),
    ("Ceftriaxone", UnitType.VIAL, "Third-generation cephalosporin injection.", 200),
    ("Ceftazidime", UnitType.VIAL, "Third-generation cephalosporin injection for Pseudomonas.", 120),
    ("Cefuroxime", UnitType.TABLET, "Second-generation cephalosporin antibiotic.", 300),
    ("Cephalexin", UnitType.CAPSULE, "First-generation cephalosporin antibiotic.", 400),
    ("Doxycycline", UnitType.CAPSULE, "Tetracycline antibiotic.", 350),
    ("Erythromycin", UnitType.TABLET, "Macrolide antibiotic.", 300),
    ("Clarithromycin", UnitType.TABLET, "Macrolide antibiotic for respiratory infections.", 280),
    ("Gentamicin", UnitType.ML, "Aminoglycoside antibiotic injection.", 90),
    ("Vancomycin", UnitType.VIAL, "Glycopeptide antibiotic for resistant Gram-positive infections.", 80),
    ("Meropenem", UnitType.VIAL, "Carbapenem antibiotic for severe infections.", 70),
    ("Cloxacillin", UnitType.CAPSULE, "Penicillinase-resistant penicillin.", 250),
    ("Nitrofurantoin", UnitType.CAPSULE, "Antibiotic for urinary tract infections.", 220),
    ("Co-trimoxazole", UnitType.TABLET, "Sulfamethoxazole/trimethoprim combination antibiotic.", 450),
    ("Tetracycline", UnitType.CAPSULE, "Broad-spectrum antibiotic.", 200),
    ("Fluconazole", UnitType.CAPSULE, "Antifungal for systemic and mucosal infections.", 300),
    ("Clotrimazole", UnitType.G, "Topical antifungal cream.", 200),
    ("Miconazole", UnitType.G, "Topical antifungal cream.", 150),
    ("Griseofulvin", UnitType.TABLET, "Antifungal for dermatophyte infections.", 100),
    ("Ketoconazole", UnitType.TABLET, "Antifungal for systemic fungal infections.", 150),
    ("Nystatin", UnitType.ML, "Antifungal oral suspension.", 180),
    ("Acyclovir", UnitType.TABLET, "Antiviral for herpes infections.", 250),
    ("Oseltamivir", UnitType.CAPSULE, "Antiviral for influenza.", 200),
    ("Lamivudine", UnitType.TABLET, "NRTI antiretroviral for HIV.", 180),
    ("Zidovudine", UnitType.CAPSULE, "NRTI antiretroviral for HIV.", 140),
    ("Artemether/Lumefantrine", UnitType.TABLET, "First-line antimalarial combination.", 500),
    ("Quinine Sulfate", UnitType.TABLET, "Antimalarial for severe/complicated malaria.", 150),
    ("Chloroquine", UnitType.TABLET, "Antimalarial and amebicide.", 180),
    ("Dihydroartemisinin/Piperaquine", UnitType.TABLET, "Antimalarial combination therapy.", 300),
    ("Omeprazole", UnitType.CAPSULE, "Proton pump inhibitor for acid reflux and ulcers.", 600),
    ("Pantoprazole", UnitType.TABLET, "Proton pump inhibitor.", 450),
    ("Esomeprazole", UnitType.CAPSULE, "Proton pump inhibitor.", 400),
    ("Ranitidine", UnitType.TABLET, "H2-receptor antagonist for acid suppression.", 500),
    ("Ondansetron", UnitType.TABLET, "Antiemetic for nausea and vomiting.", 350),
    ("Metoclopramide", UnitType.TABLET, "Antiemetic and prokinetic.", 250),
    ("Domperidone", UnitType.TABLET, "Antiemetic and prokinetic.", 250),
    ("Loperamide", UnitType.CAPSULE, "Antidiarrheal.", 220),
    ("Hyoscine Butylbromide", UnitType.TABLET, "Antispasmodic for abdominal cramps.", 300),
    ("Lactulose", UnitType.ML, "Laxative syrup.", 200),
    ("Milk of Magnesia", UnitType.ML, "Antacid and laxative suspension.", 150),
    ("Simethicone", UnitType.ML, "Antiflatulent drops.", 180),
    ("Amlodipine", UnitType.TABLET, "Calcium channel blocker for hypertension.", 500),
    ("Losartan", UnitType.TABLET, "ARB for hypertension.", 450),
    ("Valsartan", UnitType.TABLET, "ARB for hypertension and heart failure.", 400),
    ("Enalapril", UnitType.TABLET, "ACE inhibitor for hypertension.", 350),
    ("Captopril", UnitType.TABLET, "ACE inhibitor for hypertension.", 250),
    ("Atorvastatin", UnitType.TABLET, "Statin for hypercholesterolemia.", 450),
    ("Simvastatin", UnitType.TABLET, "Statin for hypercholesterolemia.", 400),
    ("Rosuvastatin", UnitType.TABLET, "Statin for hypercholesterolemia.", 350),
    ("Bisoprolol", UnitType.TABLET, "Beta-blocker for hypertension and heart failure.", 400),
    ("Atenolol", UnitType.TABLET, "Beta-blocker for hypertension.", 350),
    ("Propranolol", UnitType.TABLET, "Non-selective beta-blocker.", 250),
    ("Digoxin", UnitType.TABLET, "Cardiac glycoside for heart failure and AF.", 150),
    ("Furosemide", UnitType.TABLET, "Loop diuretic.", 400),
    ("Spironolactone", UnitType.TABLET, "Potassium-sparing diuretic.", 300),
    ("Hydrochlorothiazide", UnitType.TABLET, "Thiazide diuretic.", 350),
    ("Isosorbide Dinitrate", UnitType.TABLET, "Nitrate for angina.", 200),
    ("Nitroglycerin", UnitType.TABLET, "Sublingual nitrate for angina relief.", 180),
    ("Warfarin", UnitType.TABLET, "Anticoagulant.", 250),
    ("Heparin", UnitType.ML, "Anticoagulant injection.", 100),
    ("Clopidogrel", UnitType.TABLET, "Antiplatelet.", 350),
    ("Salbutamol", UnitType.ML, "Short-acting bronchodilator inhaler.", 300),
    ("Beclometasone", UnitType.ML, "Inhaled corticosteroid inhaler.", 250),
    ("Budesonide", UnitType.ML, "Inhaled corticosteroid for asthma.", 220),
    ("Theophylline", UnitType.TABLET, "Bronchodilator for COPD/asthma.", 150),
    ("Prednisolone", UnitType.TABLET, "Corticosteroid.", 350),
    ("Montelukast", UnitType.TABLET, "Leukotriene receptor antagonist for asthma.", 300),
    ("Dextromethorphan", UnitType.ML, "Cough suppressant syrup.", 180),
    ("Guaifenesin", UnitType.ML, "Expectorant syrup.", 200),
    ("Diazepam", UnitType.TABLET, "Benzodiazepine sedative/anxiolytic.", 250),
    ("Alprazolam", UnitType.TABLET, "Benzodiazepine anxiolytic.", 200),
    ("Lorazepam", UnitType.TABLET, "Benzodiazepine anxiolytic.", 180),
    ("Fluoxetine", UnitType.CAPSULE, "SSRI antidepressant.", 300),
    ("Sertraline", UnitType.TABLET, "SSRI antidepressant.", 300),
    ("Amitriptyline", UnitType.TABLET, "Tricyclic antidepressant.", 250),
    ("Carbamazepine", UnitType.TABLET, "Anticonvulsant.", 250),
    ("Sodium Valproate", UnitType.TABLET, "Anticonvulsant and mood stabilizer.", 220),
    ("Phenytoin", UnitType.CAPSULE, "Anticonvulsant.", 200),
    ("Levetiracetam", UnitType.TABLET, "Anticonvulsant.", 250),
    ("Haloperidol", UnitType.TABLET, "Typical antipsychotic.", 150),
    ("Levothyroxine", UnitType.TABLET, "Thyroid hormone replacement.", 400),
    ("Carbimazole", UnitType.TABLET, "Antithyroid agent.", 150),
    ("Metformin", UnitType.TABLET, "Biguanide for type 2 diabetes.", 600),
    ("Glimepiride", UnitType.TABLET, "Sulfonylurea for type 2 diabetes.", 300),
    ("Insulin Glargine", UnitType.VIAL, "Long-acting basal insulin.", 120),
]


class Command(BaseCommand):
    help = "Seeds the pharmacy with 100 common medicines."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for name, unit_type, description, base_stock in MEDICINES:
            medicine, was_created = Medicine.objects.update_or_create(
                name=name,
                defaults={
                    "unit_type": unit_type,
                    "unit_cost": round(random.uniform(2.00, 80.00), 2),
                    "stock_quantity": base_stock,
                    "low_stock_threshold": max(10, base_stock // 10),
                    "description": description,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created {created} medicines, updated {updated} "
                f"(total in inventory: {Medicine.objects.count()})."
            )
        )
