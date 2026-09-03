from django.shortcuts import render
from appointments.views import patient_required  # reuse the same role check
from . import services


@patient_required
def assistant(request):
    """
    The AI assistant page.
    GET  -> show the empty form
    POST -> analyze the patient's description and show a recommendation
    """
    recommendation = None
    problem_description = ''

    if request.method == 'POST':
        problem_description = request.POST.get('problem_description', '').strip()
        if problem_description:
            recommendation = services.get_recommendation(problem_description)

    return render(request, 'ai_assistant/assistant.html', {
        'recommendation': recommendation,
        'problem_description': problem_description,
    })
