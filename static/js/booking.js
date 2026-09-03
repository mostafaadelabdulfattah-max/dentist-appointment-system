// Booking page behavior: when the patient picks a date, fetch that
// dentist's available times for that day and show them as clickable
// buttons. Clicking a button fills the hidden "time" field and enables
// the confirm button.
//
// IMPORTANT: this JavaScript only controls what the patient SEES.
// The Django backend independently re-checks the slot is still free
// when the form is actually submitted (see appointments/services.py) —
// this JS is never the source of truth for whether a booking is allowed.

function initBooking(dentistId) {
    const dateInput = document.getElementById('date');
    const slotsContainer = document.getElementById('slots-container');
    const timeInput = document.getElementById('time');
    const confirmButton = document.getElementById('confirm-button');

    dateInput.addEventListener('change', function () {
        const selectedDate = dateInput.value;

        // Reset selection whenever the date changes
        timeInput.value = '';
        confirmButton.disabled = true;

        if (!selectedDate) {
            return;
        }

        slotsContainer.innerHTML = '<p>Loading available times...</p>';

        fetch(`/appointments/available-slots/?dentist_id=${dentistId}&date=${selectedDate}`)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.error) {
                    slotsContainer.innerHTML = `<p class="error-text">${data.error}</p>`;
                    return;
                }

                if (data.slots.length === 0) {
                    slotsContainer.innerHTML = '<p>No available times on this date. Please choose another date.</p>';
                    return;
                }

                slotsContainer.innerHTML = '';
                data.slots.forEach(function (slot) {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'slot-button';
                    button.textContent = slot;

                    button.addEventListener('click', function () {
                        document.querySelectorAll('.slot-button').forEach(function (b) {
                            b.classList.remove('selected');
                        });
                        button.classList.add('selected');

                        timeInput.value = slot;
                        confirmButton.disabled = false;
                    });

                    slotsContainer.appendChild(button);
                });
            })
            .catch(function () {
                slotsContainer.innerHTML = '<p class="error-text">Could not load available times. Please try again.</p>';
            });
    });
}
