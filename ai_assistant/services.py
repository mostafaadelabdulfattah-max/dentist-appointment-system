"""
AI Dental Assistant service layer.

IMPORTANT: this assistant does NOT diagnose medical conditions. It only
maps a patient's plain-language description to a dental SPECIALTY, then
shows REAL dentists and REAL available appointment slots for that
specialty, pulled from the database. It never invents availability.

Implementation note: this uses simple keyword matching. That's
intentional — it's easy to read, easy to test, and needs no external
API key. analyze_problem()/identify_specialty_name() is the ONLY
function that would need to change if you later swap in a real AI API
(e.g. the Anthropic API) — everything else in the project just expects
a specialty name back, so nothing else needs to know the difference.
"""

from datetime import date, timedelta

from dentists.models import Specialty, Dentist
from appointments.services import get_available_slots


# Keyword -> specialty name. Deliberately simple and readable rather
# than "clever" so it's easy to extend and explain in a demo.
SPECIALTY_KEYWORDS = {
    'General Dentistry': [
        'pain', 'ache', 'cold', 'hot', 'sensitive', 'sensitivity',
        'cavity', 'cavities', 'checkup', 'check-up', 'cleaning', 'decay',
    ],
    'Orthodontics': [
        'crooked', 'braces', 'align', 'alignment', 'bite', 'overbite',
        'underbite', 'straighten',
    ],
    'Periodontics': [
        'gum', 'gums', 'bleeding gums', 'swollen gum', 'gum disease',
    ],
    'Endodontics': [
        'root canal', 'infected tooth', 'abscess', 'nerve damage',
    ],
    'Oral Surgery': [
        'wisdom tooth', 'wisdom teeth', 'extraction', 'impacted',
        'broken tooth', 'jaw pain',
    ],
    'Pediatric Dentistry': [
        'my son', 'my daughter', 'toddler', 'baby tooth', 'my child',
    ],
}

DEFAULT_SPECIALTY_NAME = 'General Dentistry'

DISCLAIMER = (
    "This is not a diagnosis. This recommendation is only intended to "
    "help you choose an appropriate dental service."
)


def identify_specialty_name(problem_description):
    """
    Looks for keywords in the patient's description and returns the
    NAME of the best-matching specialty (most keyword matches wins).
    Falls back to General Dentistry if nothing matches — a safe
    default entry point for almost any dental concern.
    """
    text = problem_description.lower()

    best_match = None
    best_score = 0

    for specialty_name, keywords in SPECIALTY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_match = specialty_name

    return best_match or DEFAULT_SPECIALTY_NAME


def get_recommendation(problem_description, days_ahead=14):
    """
    Main entry point for the AI assistant.

    Returns a dict with:
        - specialty_name: the specialty name we identified
        - specialty: the matching Specialty object, or None if an
          admin hasn't added that specialty to the database yet
        - dentists: list of {'dentist': ..., 'slots': [...]}, using
          ONLY real data from the database
        - disclaimer: the fixed non-diagnosis disclaimer text
    """
    specialty_name = identify_specialty_name(problem_description)
    specialty = Specialty.objects.filter(name=specialty_name).first()

    dentist_results = []

    if specialty:
        dentists = Dentist.objects.filter(specialty=specialty).select_related('user')
        for dentist in dentists:
            upcoming_slots = _find_next_available_slots(dentist, days_ahead)
            if upcoming_slots:
                dentist_results.append({'dentist': dentist, 'slots': upcoming_slots})

    return {
        'specialty_name': specialty_name,
        'specialty': specialty,
        'dentists': dentist_results,
        'disclaimer': DISCLAIMER,
    }


def _find_next_available_slots(dentist, days_ahead, max_results=3):
    """
    Looks forward day-by-day (starting tomorrow) for the next few
    available slots for a dentist, reusing the EXACT SAME availability
    function the booking page uses (appointments/services.py) — so the
    AI assistant can never suggest a slot that isn't really bookable.
    """
    results = []
    today = date.today()

    for offset in range(1, days_ahead + 1):
        if len(results) >= max_results:
            break
        check_date = today + timedelta(days=offset)
        for slot in get_available_slots(dentist, check_date):
            results.append({'date': check_date, 'time': slot})
            if len(results) >= max_results:
                break

    return results
